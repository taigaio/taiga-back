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
from django.utils import timezone
from django.utils.translation import ugettext as _

from taiga.base.utils import db, text
from taiga.projects.history.services import take_snapshot
from taiga.projects.userstories.apps import (
    connect_userstories_signals,
    disconnect_userstories_signals)

from taiga.events import events
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset

from . import models


def get_userstories_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of user stories.

    :param bulk_data: List of user stories in bulk format.
    :param additional_fields: Additional fields when instantiating each user story.

    :return: List of `UserStory` instances.
    """
    return [models.UserStory(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_userstories_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create user stories from `bulk_data`.

    :param bulk_data: List of user stories in bulk format.
    :param callback: Callback to execute after each user story save.
    :param additional_fields: Additional fields when instantiating each user story.

    :return: List of created `Task` instances.
    """
    userstories = get_userstories_from_bulk(bulk_data, **additional_fields)

    disconnect_userstories_signals()

    try:
        db.save_in_bulk(userstories, callback, precall)
    finally:
        connect_userstories_signals()

    return userstories


def update_userstories_order_in_bulk(bulk_data:list, field:str, project:object):
    """
    Update the order of some user stories.
    `bulk_data` should be a list of tuples with the following format:

    [(<user story id>, {<field>: <value>, ...}), ...]
    """
    user_story_ids = []
    new_order_values = []
    for us_data in bulk_data:
        user_story_ids.append(us_data["us_id"])
        new_order_values.append({field: us_data["order"]})

    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=project.pk)

    db.update_in_bulk_with_ids(user_story_ids, new_order_values, model=models.UserStory)


def snapshot_userstories_in_bulk(bulk_data, user):
    user_story_ids = []
    for us_data in bulk_data:
        try:
            us = models.UserStory.objects.get(pk=us_data['us_id'])
            take_snapshot(us, user=user)
        except models.UserStory.DoesNotExist:
            pass


def calculate_userstory_is_closed(user_story):
    if user_story.status is None:
        return False

    if user_story.tasks.count() == 0:
        return user_story.status is not None and user_story.status.is_closed

    if all([task.status is not None and task.status.is_closed for task in user_story.tasks.all()]):
        return True

    return False


def close_userstory(us):
    if not us.is_closed:
        us.is_closed = True
        us.finish_date = timezone.now()
        us.save(update_fields=["is_closed", "finish_date"])


def open_userstory(us):
    if us.is_closed:
        us.is_closed = False
        us.finish_date = None
        us.save(update_fields=["is_closed", "finish_date"])


def userstories_to_csv(project,queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "sprint", "sprint_estimated_start",
                  "sprint_estimated_finish", "owner", "owner_full_name", "assigned_to",
                  "assigned_to_full_name", "status", "is_closed"]

    roles = project.roles.filter(computable=True).order_by('slug')
    for role in roles:
        fieldnames.append("{}-points".format(role.slug))

    fieldnames.append("total-points")

    fieldnames += ["backlog_order", "sprint_order", "kanban_order",
                   "created_date", "modified_date", "finish_date",
                   "client_requirement", "team_requirement", "attachments",
                   "generated_from_issue", "external_reference", "tasks",
                   "tags","watchers", "voters"]

    custom_attrs = project.userstorycustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related("role_points",
                                         "role_points__points",
                                         "role_points__role",
                                         "tasks",
                                         "attachments",
                                         "custom_attributes_values")
    queryset = queryset.select_related("milestone",
                                       "project",
                                       "status",
                                       "owner",
                                       "assigned_to",
                                       "generated_from_issue")

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for us in queryset:
        row = {
            "ref": us.ref,
            "subject": us.subject,
            "description": us.description,
            "sprint": us.milestone.name if us.milestone else None,
            "sprint_estimated_start": us.milestone.estimated_start if us.milestone else None,
            "sprint_estimated_finish": us.milestone.estimated_finish if us.milestone else None,
            "owner": us.owner.username if us.owner else None,
            "owner_full_name": us.owner.get_full_name() if us.owner else None,
            "assigned_to": us.assigned_to.username if us.assigned_to else None,
            "assigned_to_full_name": us.assigned_to.get_full_name() if us.assigned_to else None,
            "status": us.status.name if us.status else None,
            "is_closed": us.is_closed,
            "backlog_order": us.backlog_order,
            "sprint_order": us.sprint_order,
            "kanban_order": us.kanban_order,
            "created_date": us.created_date,
            "modified_date": us.modified_date,
            "finish_date": us.finish_date,
            "client_requirement": us.client_requirement,
            "team_requirement": us.team_requirement,
            "attachments": us.attachments.count(),
            "generated_from_issue": us.generated_from_issue.ref if us.generated_from_issue else None,
            "external_reference": us.external_reference,
            "tasks": ",".join([str(task.ref) for task in us.tasks.all()]),
            "tags": ",".join(us.tags or []),
            "watchers": us.watchers,
            "voters": us.total_voters,
        }

        us_role_points_by_role_id = {us_rp.role.id: us_rp.points.value for us_rp in us.role_points.all()}
        for role in roles:
            row["{}-points".format(role.slug)] = us_role_points_by_role_id.get(role.id, 0)

        row['total-points'] = us.get_total_points()

        for custom_attr in custom_attrs:
            value = us.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            row[custom_attr.name] = value

        writer.writerow(row)

    return csv_data


def _get_userstories_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
      SELECT "projects_userstorystatus"."id",
             "projects_userstorystatus"."name",
             "projects_userstorystatus"."color",
             "projects_userstorystatus"."order",
             (SELECT count(*)
                FROM "userstories_userstory"
                     INNER JOIN "projects_project" ON
                                ("userstories_userstory"."project_id" = "projects_project"."id")
               WHERE {where} AND "userstories_userstory"."status_id" = "projects_userstorystatus"."id")
        FROM "projects_userstorystatus"
       WHERE "projects_userstorystatus"."project_id" = %s
    ORDER BY "projects_userstorystatus"."order";
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


def _get_userstories_assigned_to(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT assigned_to_id,  count(assigned_to_id) count
                  FROM "userstories_userstory"
            INNER JOIN "projects_project" ON ("userstories_userstory"."project_id" = "projects_project"."id")
                 WHERE {where} AND "userstories_userstory"."assigned_to_id" IS NOT NULL
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

        -- unassigned userstories
        UNION

                 SELECT NULL user_id, NULL, NULL, count(coalesce(assigned_to_id, -1)) count
                   FROM "userstories_userstory"
             INNER JOIN "projects_project" ON ("userstories_userstory"."project_id" = "projects_project"."id")
                  WHERE {where} AND "userstories_userstory"."assigned_to_id" IS NULL
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

    # If there was no userstory with null assigned_to we manually add it
    if not none_valued_added:
        result.append({
            "id": None,
            "full_name": "",
            "count": 0,
        })

    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT "userstories_userstory"."owner_id" owner_id,  count(coalesce("userstories_userstory"."owner_id", -1)) count
                  FROM "userstories_userstory"
            INNER JOIN "projects_project" ON ("userstories_userstory"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY "userstories_userstory"."owner_id"
        )

                 SELECT "projects_membership"."user_id" id,
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."owner_id")
             INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE ("projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL)

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


def _get_userstories_tags(queryset):
    tags = []
    for t_list in queryset.values_list("tags", flat=True):
        if t_list is None:
            continue
        tags += list(t_list)

    tags = [{"name":e, "count":tags.count(e)} for e in set(tags)]

    return sorted(tags, key=itemgetter("name"))


def get_userstories_filters_data(project, querysets):
    """
    Given a project and an userstories queryset, return a simple data structure
    of all possible filters for the userstories in the queryset.
    """
    data = OrderedDict([
        ("statuses", _get_userstories_statuses(project, querysets["statuses"])),
        ("assigned_to", _get_userstories_assigned_to(project, querysets["assigned_to"])),
        ("owners", _get_userstories_owners(project, querysets["owners"])),
        ("tags", _get_userstories_tags(querysets["tags"])),
    ])

    return data
