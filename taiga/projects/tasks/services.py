# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import csv
import io
from collections import OrderedDict
from operator import itemgetter
from contextlib import closing

from django.db import connection
from django.utils.translation import ugettext as _

from taiga.base.utils import db, text
from taiga.projects.history.services import take_snapshot
from taiga.projects.services import apply_order_updates
from taiga.projects.tasks.apps import connect_tasks_signals
from taiga.projects.tasks.apps import disconnect_tasks_signals
from taiga.events import events
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset

from . import models


#####################################################
# Bulk actions
#####################################################

def get_tasks_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of tasks.

    :param bulk_data: List of tasks in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Task` instances.
    """
    return [models.Task(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_tasks_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create tasks from `bulk_data`.

    :param bulk_data: List of tasks in bulk format.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Task` instances.
    """
    tasks = get_tasks_from_bulk(bulk_data, **additional_fields)

    disconnect_tasks_signals()

    try:
        db.save_in_bulk(tasks, callback, precall)
    finally:
        connect_tasks_signals()

    return tasks


def update_tasks_order_in_bulk(bulk_data: list, field: str, project: object,
                               user_story: object=None, status: object=None, milestone: object=None):
    """
    Updates the order of the tasks specified adding the extra updates needed
    to keep consistency.

    [{'task_id': <value>, 'order': <value>}, ...]
    """
    tasks = project.tasks.all()
    if user_story is not None:
        tasks = tasks.filter(user_story=user_story)
    if status is not None:
        tasks = tasks.filter(status=status)
    if milestone is not None:
        tasks = tasks.filter(milestone=milestone)

    task_orders = {task.id: getattr(task, field) for task in tasks}
    new_task_orders = {e["task_id"]: e["order"] for e in bulk_data}
    apply_order_updates(task_orders, new_task_orders)

    task_ids = task_orders.keys()
    events.emit_event_for_ids(ids=task_ids,
                              content_type="tasks.task",
                              projectid=project.pk)

    db.update_attr_in_bulk_for_ids(task_orders, field, models.Task)
    return task_orders


def snapshot_tasks_in_bulk(bulk_data, user):
    for task_data in bulk_data:
        try:
            task = models.Task.objects.get(pk=task_data['task_id'])
            take_snapshot(task, user=user)
        except models.Task.DoesNotExist:
            pass


#####################################################
# CSV
#####################################################

def tasks_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "user_story", "sprint", "sprint_estimated_start",
                  "sprint_estimated_finish", "owner", "owner_full_name", "assigned_to",
                  "assigned_to_full_name", "status", "is_iocaine", "is_closed", "us_order",
                  "taskboard_order", "attachments", "external_reference", "tags", "watchers", "voters",
                  "created_date", "modified_date", "finished_date"]

    custom_attrs = project.taskcustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related("attachments",
                                         "custom_attributes_values")
    queryset = queryset.select_related("milestone",
                                       "owner",
                                       "assigned_to",
                                       "status",
                                       "project")

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for task in queryset:
        task_data = {
            "ref": task.ref,
            "subject": task.subject,
            "description": task.description,
            "user_story": task.user_story.ref if task.user_story else None,
            "sprint": task.milestone.name if task.milestone else None,
            "sprint_estimated_start": task.milestone.estimated_start if task.milestone else None,
            "sprint_estimated_finish": task.milestone.estimated_finish if task.milestone else None,
            "owner": task.owner.username if task.owner else None,
            "owner_full_name": task.owner.get_full_name() if task.owner else None,
            "assigned_to": task.assigned_to.username if task.assigned_to else None,
            "assigned_to_full_name": task.assigned_to.get_full_name() if task.assigned_to else None,
            "status": task.status.name if task.status else None,
            "is_iocaine": task.is_iocaine,
            "is_closed": task.status is not None and task.status.is_closed,
            "us_order": task.us_order,
            "taskboard_order": task.taskboard_order,
            "attachments": task.attachments.count(),
            "external_reference": task.external_reference,
            "tags": ",".join(task.tags or []),
            "watchers": task.watchers,
            "voters": task.total_voters,
            "created_date": task.created_date,
            "modified_date": task.modified_date,
            "finished_date": task.finished_date,
        }
        for custom_attr in custom_attrs:
            value = task.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            task_data[custom_attr.name] = value

        writer.writerow(task_data)

    return csv_data


#####################################################
# Api filter data
#####################################################

def _get_tasks_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
      SELECT "projects_taskstatus"."id",
             "projects_taskstatus"."name",
             "projects_taskstatus"."color",
             "projects_taskstatus"."order",
             (SELECT count(*)
                FROM "tasks_task"
                     INNER JOIN "projects_project" ON
                                ("tasks_task"."project_id" = "projects_project"."id")
               WHERE {where} AND "tasks_task"."status_id" = "projects_taskstatus"."id")
        FROM "projects_taskstatus"
       WHERE "projects_taskstatus"."project_id" = %s
    ORDER BY "projects_taskstatus"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": color,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def _get_tasks_assigned_to(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT assigned_to_id,  count(assigned_to_id) count
                  FROM "tasks_task"
            INNER JOIN "projects_project" ON ("tasks_task"."project_id" = "projects_project"."id")
                 WHERE {where} AND "tasks_task"."assigned_to_id" IS NOT NULL
              GROUP BY assigned_to_id
        )

                 SELECT "projects_membership"."user_id" user_id,
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."assigned_to_id")
             INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- unassigned tasks
        UNION

                 SELECT NULL user_id, NULL, NULL, count(coalesce(assigned_to_id, -1)) count
                   FROM "tasks_task"
             INNER JOIN "projects_project" ON ("tasks_task"."project_id" = "projects_project"."id")
                  WHERE {where} AND "tasks_task"."assigned_to_id" IS NULL
               GROUP BY assigned_to_id
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count in rows:
        result.append({
            "id": id,
            "full_name": full_name or username or "",
            "count": count,
        })

        if id is None:
            none_valued_added = True

    # If there was no task with null assigned_to we manually add it
    if not none_valued_added:
        result.append({
            "id": None,
            "full_name": "",
            "count": 0,
        })

    return sorted(result, key=itemgetter("full_name"))


def _get_tasks_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT "tasks_task"."owner_id" owner_id,
                       count(coalesce("tasks_task"."owner_id", -1)) count
                  FROM "tasks_task"
            INNER JOIN "projects_project" ON ("tasks_task"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY "tasks_task"."owner_id"
        )

                 SELECT "projects_membership"."user_id" id,
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."owner_id")
             INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- System users
        UNION

                 SELECT "users_user"."id" user_id,
                        "users_user"."full_name" full_name,
                        "users_user"."username" username,
                        COALESCE("counters".count, 0) count
                   FROM users_user
        LEFT OUTER JOIN counters ON ("users_user"."id" = "counters"."owner_id")
                  WHERE ("users_user"."is_system" IS TRUE)
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, username, count in rows:
        if count > 0:
            result.append({
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
            })
    return sorted(result, key=itemgetter("full_name"))


def _get_tasks_tags(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH tasks_tags AS (
                    SELECT tag,
                           COUNT(tag) counter FROM (
                                SELECT UNNEST(tasks_task.tags) tag
                                  FROM tasks_task
                            INNER JOIN projects_project
                                        ON (tasks_task.project_id = projects_project.id)
                                 WHERE {where}) tags
                  GROUP BY tag),
             project_tags AS (
                    SELECT reduce_dim(tags_colors) tag_color
                      FROM projects_project
                     WHERE id=%s)

      SELECT tag_color[1] tag, COALESCE(tasks_tags.counter, 0) counter
        FROM project_tags
   LEFT JOIN tasks_tags ON project_tags.tag_color[1] = tasks_tags.tag
    ORDER BY tag
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for name, count in rows:
        result.append({
            "name": name,
            "count": count,
        })
    return sorted(result, key=itemgetter("name"))


def get_tasks_filters_data(project, querysets):
    """
    Given a project and an tasks queryset, return a simple data structure
    of all possible filters for the tasks in the queryset.
    """
    data = OrderedDict([
        ("statuses", _get_tasks_statuses(project, querysets["statuses"])),
        ("assigned_to", _get_tasks_assigned_to(project, querysets["assigned_to"])),
        ("owners", _get_tasks_owners(project, querysets["owners"])),
        ("tags", _get_tasks_tags(project, querysets["tags"])),
    ])

    return data
