# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from typing import List, Optional

import csv
import io
from collections import OrderedDict
from operator import itemgetter
from contextlib import closing

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from psycopg2.extras import execute_values

from taiga.base.utils import db, text
from taiga.celery import app
from taiga.events import events
from taiga.projects.history.services import take_snapshot
from taiga.projects.models import Project, UserStoryStatus, Swimlane
from taiga.projects.milestones.models import Milestone
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.services import apply_order_updates
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.apps import connect_userstories_signals
from taiga.projects.userstories.apps import disconnect_userstories_signals
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.users.models import User
from taiga.users.gravatar import get_gravatar_id
from taiga.users.services import get_big_photo_url, get_photo_url

from . import models


#####################################################
# Bulk actions
#####################################################

def get_userstories_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of user stories.

    :param bulk_data: List of user stories in bulk format.
    :param additional_fields: Additional fields when instantiating each user
    story.

    :return: List of `UserStory` instances.
    """
    return [models.UserStory(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_userstories_in_bulk(bulk_data, callback=None, precall=None,
                               **additional_fields):
    """Create user stories from `bulk_data`.

    :param bulk_data: List of user stories in bulk format.
    :param callback: Callback to execute after each user story save.
    :param additional_fields: Additional fields when instantiating each user
    story.

    :return: List of created `Task` instances.
    """
    userstories = get_userstories_from_bulk(bulk_data, **additional_fields)
    project = additional_fields.get("project")
    disconnect_userstories_signals()

    try:
        db.save_in_bulk(userstories, callback, precall)
        project.update_role_points(user_stories=userstories)
    finally:
        connect_userstories_signals()

    return userstories


def update_userstories_order_in_bulk(bulk_data: list, field: str,
                                     project: object,
                                     status: object = None,
                                     milestone: object = None):
    """
    Updates the order of the userstories specified adding the extra updates
    needed to keep consistency.
    `bulk_data` should be a list of dicts with the following format:
    `field` is the order field used

    [{'us_id': <value>, 'order': <value>}, ...]
    """
    user_stories = project.user_stories.all()
    if status is not None:
        user_stories = user_stories.filter(status=status)
    if milestone is not None:
        user_stories = user_stories.filter(milestone=milestone)

    us_orders = {us.id: getattr(us, field) for us in user_stories}
    new_us_orders = {e["us_id"]: e["order"] for e in bulk_data}
    apply_order_updates(us_orders, new_us_orders, remove_equal_original=True)

    user_story_ids = us_orders.keys()
    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=project.pk)
    db.update_attr_in_bulk_for_ids(us_orders, field, models.UserStory)
    return us_orders


def reset_userstories_kanban_order_in_bulk(project: Project,
                                           bulk_userstories: List[int]):
    """
    Reset the order of the userstories specified adding the extra updates
    needed to keep consistency.

     - `bulk_userstories` should be a list of user stories IDs
    """
    base_order = models.UserStory.NEW_KANBAN_ORDER()
    data = ((id, base_order + index) for index, id in enumerate(bulk_userstories))

    sql = """
    UPDATE userstories_userstory
       SET kanban_order = tmp.new_kanban_order::BIGINT
      FROM (VALUES %s) AS tmp (id, new_kanban_order)
     WHERE tmp.id = userstories_userstory.id
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, data)

    ## Sent events of updated stories
    events.emit_event_for_ids(ids=bulk_userstories,
                              content_type="userstories.userstory",
                              projectid=project.id)


def update_userstories_backlog_or_sprint_order_in_bulk(user: User,
                                                       project: Project,
                                                       bulk_userstories: List[int],
                                                       before_userstory: Optional[models.UserStory] = None,
                                                       after_userstory: Optional[models.UserStory] = None,
                                                       milestone: Optional[Milestone] = None):
    """
    Updates the order of the userstories specified adding the extra updates
    needed to keep consistency.

    Note: `after_userstory_id` and `before_userstory_id` are mutually exclusive;
          you can use only one at a given request. They can be both None which
          means "at the beginning of is cell"

     - `bulk_userstories` should be a list of user stories IDs
    """
    # Get ids from milestones affected
    milestones_ids = set(project.milestones.filter(user_stories__in=bulk_userstories).values_list('id', flat=True))
    if milestone:
        milestones_ids.add(milestone.id)

    order_param = "backlog_order"

    # filter user stories from milestone
    user_stories = project.user_stories.all()
    if milestone is not None:
         user_stories = user_stories.filter(milestone=milestone)
         order_param = "sprint_order"
    else:
         user_stories = user_stories.filter(milestone__isnull=True)

    # exclude moved user stories
    user_stories = user_stories.exclude(id__in=bulk_userstories)

    # if before_userstory, get it and all elements before too:
    if before_userstory:
        user_stories = (user_stories.filter(**{f"{order_param}__gte": getattr(before_userstory, order_param)}))
    # if after_userstory, exclude it and get only elements after it:
    elif after_userstory:
        user_stories = (user_stories.exclude(id=after_userstory.id)
                                    .filter(**{f"{order_param}__gte": getattr(after_userstory, order_param)}))

    # sort and get only ids
    user_story_ids = (user_stories.order_by(order_param, "id")
                                  .values_list('id', flat=True))

    # append moved user stories
    user_story_ids = bulk_userstories + list(user_story_ids)

    # calculate the start order
    if before_userstory:
        # order start with the before_userstory order
        start_order = getattr(before_userstory, order_param)
    elif after_userstory:
        # order start after the after_userstory order
        start_order = getattr(after_userstory, order_param) + 1
    else:
        # move at the beggining of the column if there is no after and before
        start_order = 1

    # prepare rest of data
    total_user_stories = len(user_story_ids)
    user_story_orders = range(start_order, start_order + total_user_stories)

    data = tuple(zip(user_story_ids,
                     user_story_orders))

    # execute query for update milestone and backlog or sprint order
    sql = f"""
    UPDATE userstories_userstory
       SET {order_param} = tmp.new_order::BIGINT
      FROM (VALUES %s) AS tmp (id, new_order)
     WHERE tmp.id = userstories_userstory.id
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, data)

    # execute query for update milestone for user stories and its tasks
    bulk_userstories_objects = project.user_stories.filter(id__in=bulk_userstories)
    bulk_userstories_objects.update(milestone=milestone)
    project.tasks.filter(user_story__in=bulk_userstories).update(milestone=milestone)

    # Generate snapshots for user stories and tasks and calculate if aafected milestones
    # are cosed or open now.
    if settings.CELERY_ENABLED:
        _async_tasks_after_backlog_or_sprint_order_change.delay(bulk_userstories, milestones_ids, user.id)
    else:
        _async_tasks_after_backlog_or_sprint_order_change(bulk_userstories, milestones_ids, user.id)

    # Sent events of updated stories
    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=project.pk)

    # Generate response with modified info
    res = ({
        "id": id,
        "milestone": milestone.id if milestone else None,
        order_param: order
    } for (id, order) in data)
    return res


@app.task
def _async_tasks_after_backlog_or_sprint_order_change(userstories_ids, milestones_ids, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    # Take snapshots for user stories and their taks
    for userstory in  models.UserStory.objects.filter(id__in=userstories_ids):
        take_snapshot(userstory, user=user)

        for task in userstory.tasks.all():
            take_snapshot(task, user=user)

    # Check if milestones are open or closed after stories are moved
    for milestone in  Milestone.objects.filter(id__in=milestones_ids):
        _recalculate_is_closed_for_milestone(milestone)



def update_userstories_kanban_order_in_bulk(user: User,
                                            project: Project,
                                            status: UserStoryStatus,
                                            bulk_userstories: List[int],
                                            before_userstory: Optional[models.UserStory] = None,
                                            after_userstory: Optional[models.UserStory] = None,
                                            swimlane: Optional[Swimlane] = None):
    """
    Updates the order of the userstories specified adding the extra updates
    needed to keep consistency.

    Note: `after_userstory_id` and `before_userstory_id` are mutually exclusive;
          you can use only one at a given request. They can be both None which
          means "at the beginning of is cell"

     - `bulk_userstories` should be a list of user stories IDs
    """


    # filter user stories from status and swimlane
    user_stories = project.user_stories.filter(status=status)
    if swimlane is not None:
         user_stories = user_stories.filter(swimlane=swimlane)
    else:
         user_stories = user_stories.filter(swimlane__isnull=True)

    # exclude moved user stories
    user_stories = user_stories.exclude(id__in=bulk_userstories)

    # if before_userstory, get it and all elements before too:
    if before_userstory:
        user_stories = (user_stories.filter(kanban_order__gte=before_userstory.kanban_order))
    # if after_userstory, exclude it and get only elements after it:
    elif after_userstory:
        user_stories = (user_stories.exclude(id=after_userstory.id)
                                    .filter(kanban_order__gte=after_userstory.kanban_order))

    # sort and get only ids
    user_story_ids = (user_stories.order_by("kanban_order", "id")
                                  .values_list('id', flat=True))

    # append moved user stories
    user_story_ids = bulk_userstories + list(user_story_ids)

    # calculate the start order
    if before_userstory:
        # order start with the before_userstory order
        start_order = before_userstory.kanban_order
    elif after_userstory:
        # order start after the after_userstory order
        start_order = after_userstory.kanban_order + 1
    else:
        # move at the beggining of the column if there is no after and before
        start_order = 1

    # prepare rest of data
    total_user_stories = len(user_story_ids)
    user_story_kanban_orders = range(start_order, start_order + total_user_stories)

    data = tuple(zip(user_story_ids,
                     user_story_kanban_orders))

    # execute query for update kanban_order
    sql = """
    UPDATE userstories_userstory
       SET kanban_order = tmp.new_kanban_order::BIGINT
      FROM (VALUES %s) AS tmp (id, new_kanban_order)
     WHERE tmp.id = userstories_userstory.id
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, data)

    # execute query for update status, swimlane and kanban_order
    bulk_userstories_objects = project.user_stories.filter(id__in=bulk_userstories)
    bulk_userstories_objects.update(status=status, swimlane=swimlane)

    # Update is_closed attr for user stories and related milestones
    if settings.CELERY_ENABLED:
        _async_tasks_after_kanban_order_change.delay(bulk_userstories, user.id)
    else:
        _async_tasks_after_kanban_order_change(bulk_userstories, user.id)

    # Sent events of updated stories
    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=project.pk)

    # Generate response with modified info
    res = ({
        "id": id,
        "swimlane": swimlane.id if swimlane else None,
        "status": status.id,
        "kanban_order": kanban_order
    } for (id, kanban_order) in data)
    return res


@app.task
def _async_tasks_after_kanban_order_change(userstories_ids, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    for userstory in  models.UserStory.objects.filter(id__in=userstories_ids):
        recalculate_is_closed_for_userstory_and_its_milestone(userstory)
        # Generate the history entity
        take_snapshot(userstory, user=user)


def update_userstories_milestone_in_bulk(bulk_data: list, milestone: object):
    """
    Update the milestone and the milestone order of some user stories adding
    the extra orders needed to keep consistency.
    `bulk_data` should be a list of dicts with the following format:
    [{'us_id': <value>, 'order': <value>}, ...]
    """
    user_stories = milestone.user_stories.all()
    us_orders = {us.id: getattr(us, "sprint_order") for us in user_stories}
    new_us_orders = {}
    for e in bulk_data:
        new_us_orders[e["us_id"]] = e["order"]
        # The base orders where we apply the new orders must containg all
        # the values
        us_orders[e["us_id"]] = e["order"]

    apply_order_updates(us_orders, new_us_orders)

    us_milestones = {e["us_id"]: milestone.id for e in bulk_data}
    user_story_ids = us_milestones.keys()

    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=milestone.project.pk)

    db.update_attr_in_bulk_for_ids(us_milestones, "milestone_id",
                                   model=models.UserStory)
    db.update_attr_in_bulk_for_ids(us_orders, "sprint_order", models.UserStory)

    # Updating the milestone for the tasks
    Task.objects.filter(
        user_story_id__in=[e["us_id"] for e in bulk_data]).update(
        milestone=milestone)

    return us_orders


def snapshot_userstories_in_bulk(bulk_data, user):
    for us_data in bulk_data:
        try:
            us = models.UserStory.objects.get(pk=us_data['us_id'])
            take_snapshot(us, user=user)
        except models.UserStory.DoesNotExist:
            pass


#####################################################
# Open/Close calcs
#####################################################

def calculate_userstory_is_closed(user_story):
    if user_story.status is None:
        return False

    if user_story.tasks.count() == 0:
        return user_story.status is not None and user_story.status.is_closed

    if all([task.status is not None and task.status.is_closed for task in
            user_story.tasks.all()]):
        return True

    return False


def close_userstory(us):
    if not us.is_closed:
        us.is_closed = True
        us.finish_date = timezone.now()
        us.save(update_fields=["is_closed", "finish_date"])
        return True
    return False


def open_userstory(us):
    if us.is_closed:
        us.is_closed = False
        us.finish_date = None
        us.save(update_fields=["is_closed", "finish_date"])
        return True
    return False



def recalculate_is_closed_for_userstory_and_its_milestone(userstory):
    """
    Check and update the open or closed condition for the userstory and its milestone.

    NOTE: [1] This method is useful if the userstory update operation has been done without
              using the ORM (pre_save/post_save model signals).
          [2] Do not use it if the milestone has been previously updated.
    """
    has_changed = False
    # Update is_close attr for the user story
    if calculate_userstory_is_closed(userstory):
        has_changed = close_userstory(userstory)
    else:
        has_changed = open_userstory(userstory)

    if has_changed and userstory.milestone_id:
        _recalculate_is_closed_for_milestone(userstory.milestone)


def _recalculate_is_closed_for_milestone(milestone):
    """
    Check and update the open or closed condition for the milestone.

    NOTE: [1] This method is useful if the userstory update operation has been done without
              using the ORM (pre_save/post_save model signals).
    """
    from taiga.projects.milestones import services as milestone_service

    # Update is_close attr for the milestone
    if milestone_service.calculate_milestone_is_closed(milestone):
        milestone_service.close_milestone(milestone)
    else:
        milestone_service.open_milestone(milestone)

#####################################################
# CSV
#####################################################

def userstories_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["id", "ref", "subject", "description", "sprint_id", "sprint",
                  "sprint_estimated_start", "sprint_estimated_finish", "owner",
                  "owner_full_name", "assigned_to", "assigned_to_full_name",
                  "assigned_users", "assigned_users_full_name", "status",
                  "is_closed", "swimlane"]

    roles = project.roles.filter(computable=True).order_by('slug')
    for role in roles:
        fieldnames.append("{}-points".format(role.slug))

    fieldnames.append("total-points")

    fieldnames += ["backlog_order", "sprint_order", "kanban_order",
                   "created_date", "modified_date", "finish_date",
                   "client_requirement", "team_requirement", "attachments",
                   "generated_from_issue", "generated_from_task", "from_task_ref",
                   "external_reference", "tasks", "tags", "watchers", "voters",
                   "due_date", "due_date_reason", "epics"]

    custom_attrs = project.userstorycustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related("role_points",
                                         "role_points__points",
                                         "role_points__role",
                                         "tasks",
                                         "epics",
                                         "attachments",
                                         "custom_attributes_values")
    queryset = queryset.select_related("milestone",
                                       "project",
                                       "status",
                                       "owner",
                                       "assigned_to",
                                       "generated_from_issue",
                                       "generated_from_task")

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for us in queryset:
        row = {
            "id": us.id,
            "ref": us.ref,
            "subject": us.subject,
            "description": us.description,
            "sprint_id": us.milestone.id if us.milestone else None,
            "sprint": us.milestone.name if us.milestone else None,
            "sprint_estimated_start": us.milestone.estimated_start if
            us.milestone else None,
            "sprint_estimated_finish": us.milestone.estimated_finish if
            us.milestone else None,
            "owner": us.owner.username if us.owner else None,
            "owner_full_name": us.owner.get_full_name() if us.owner else None,
            "assigned_to": us.assigned_to.username if us.assigned_to else None,
            "assigned_to_full_name": us.assigned_to.get_full_name() if
            us.assigned_to else None,
            "assigned_users": ",".join(
                [assigned_user.username for assigned_user in
                 us.assigned_users.all()]),
            "assigned_users_full_name": ",".join(
                [assigned_user.get_full_name() for assigned_user in
                 us.assigned_users.all()]),
            "status": us.status.name if us.status else None,
            "is_closed": us.is_closed,
            "swimlane": us.swimlane.name if us.swimlane else None,
            "backlog_order": us.backlog_order,
            "sprint_order": us.sprint_order,
            "kanban_order": us.kanban_order,
            "created_date": us.created_date,
            "modified_date": us.modified_date,
            "finish_date": us.finish_date,
            "client_requirement": us.client_requirement,
            "team_requirement": us.team_requirement,
            "attachments": us.attachments.count(),
            "generated_from_issue": us.generated_from_issue.ref if
            us.generated_from_issue else None,
            "generated_from_task": us.generated_from_task.ref if
            us.generated_from_task else None,
            "from_task_ref": us.from_task_ref,
            "external_reference": us.external_reference,
            "tasks": ",".join([str(task.ref) for task in us.tasks.all()]),
            "tags": ",".join(us.tags or []),
            "watchers": us.watchers,
            "voters": us.total_voters,
            "due_date": us.due_date,
            "due_date_reason": us.due_date_reason,
            "epics": ",".join([str(epic.ref) for epic in us.epics.all()]),
        }

        us_role_points_by_role_id = {us_rp.role.id: us_rp.points.value for
                                     us_rp in us.role_points.all()}
        for role in roles:
            row["{}-points".format(role.slug)] = \
                us_role_points_by_role_id.get(role.id, 0)

        row['total-points'] = us.get_total_points()

        for custom_attr in custom_attrs:
            if not hasattr(us, "custom_attributes_values"):
                continue
            value = us.custom_attributes_values.attributes_values.get(
                str(custom_attr.id), None)
            row[custom_attr.name] = value

        writer.writerow(row)

    return csv_data


#####################################################
# Api filter data
#####################################################

def _get_userstories_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
     WITH "us_counters" AS (
         SELECT DISTINCT "userstories_userstory"."status_id" "status_id",
                         "userstories_userstory"."id" "us_id"
                    FROM "userstories_userstory"
              INNER JOIN "projects_project"
                      ON ("userstories_userstory"."project_id" = "projects_project"."id")
         LEFT OUTER JOIN "epics_relateduserstory"
                      ON "userstories_userstory"."id" = "epics_relateduserstory"."user_story_id"
         LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                   WHERE {where}
            ),
             "counters" AS (
                  SELECT "status_id",
                         COUNT("status_id") "count"
                    FROM "us_counters"
                GROUP BY "status_id"
            )

                 SELECT "projects_userstorystatus"."id",
                        "projects_userstorystatus"."name",
                        "projects_userstorystatus"."color",
                        "projects_userstorystatus"."order",
                        COALESCE("counters"."count", 0)
                   FROM "projects_userstorystatus"
        LEFT OUTER JOIN "counters"
                     ON "counters"."status_id" = "projects_userstorystatus"."id"
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
     WITH "us_counters" AS (
         SELECT DISTINCT "userstories_userstory"."assigned_to_id" "assigned_to_id",
                         "userstories_userstory"."id" "us_id"
                    FROM "userstories_userstory"
              INNER JOIN "projects_project"
                      ON ("userstories_userstory"."project_id" = "projects_project"."id")
                INNER JOIN "projects_userstorystatus"
                    ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
         LEFT OUTER JOIN "epics_relateduserstory"
                      ON "userstories_userstory"."id" = "epics_relateduserstory"."user_story_id"
         LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                   WHERE {where}
            ),

            "counters" AS (
                 SELECT "assigned_to_id",
                        COUNT("assigned_to_id")
                   FROM "us_counters"
               GROUP BY "assigned_to_id"
            )

                 SELECT "projects_membership"."user_id" "user_id",
                        "users_user"."full_name" "full_name",
                        "users_user"."username" "username",
                        COALESCE("counters".count, 0) "count"
                   FROM "projects_membership"
        LEFT OUTER JOIN "counters"
                     ON ("projects_membership"."user_id" = "counters"."assigned_to_id")
             INNER JOIN "users_user"
                     ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- unassigned userstories
        UNION

                 SELECT NULL "user_id",
                        NULL "full_name",
                        NULL "username",
                        count(coalesce("assigned_to_id", -1)) "count"
                   FROM "userstories_userstory"
             INNER JOIN "projects_project"
                     ON ("userstories_userstory"."project_id" = "projects_project"."id")
             INNER JOIN "projects_userstorystatus"
                    ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
        LEFT OUTER JOIN "epics_relateduserstory"
                     ON ("userstories_userstory"."id" = "epics_relateduserstory"."user_story_id")
        LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                  WHERE {where} AND "userstories_userstory"."assigned_to_id" IS NULL
               GROUP BY "assigned_to_id"
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


def _get_userstories_assigned_users(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
     WITH "us_counters" AS (
         SELECT DISTINCT COALESCE("userstories_userstory_assigned_users"."user_id",
            "userstories_userstory"."assigned_to_id") as "assigned_user_id",
                "userstories_userstory"."id" "us_id"
                    FROM "userstories_userstory"
              LEFT JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory_assigned_users"."userstory_id" = "userstories_userstory"."id"
              INNER JOIN "projects_project"
                      ON ("userstories_userstory"."project_id" = "projects_project"."id")
                INNER JOIN "projects_userstorystatus"
                    ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
              LEFT OUTER JOIN "epics_relateduserstory"
                      ON "userstories_userstory"."id" = "epics_relateduserstory"."user_story_id"
                   WHERE {where}
            ),

            "counters" AS (
                 SELECT "assigned_user_id",
                        COUNT("assigned_user_id")
                   FROM "us_counters"
               GROUP BY "assigned_user_id"
            )

                 SELECT "projects_membership"."user_id" "user_id",
                        "users_user"."full_name" "full_name",
                        "users_user"."username" "username",
                        COALESCE("counters".count, 0) "count",
                        "users_user"."photo" "photo",
                        "users_user"."email" "email"
                   FROM "projects_membership"
        LEFT OUTER JOIN "counters"
                     ON ("projects_membership"."user_id" = "counters"."assigned_user_id")
             INNER JOIN "users_user"
                     ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- unassigned userstories
        UNION

                 SELECT NULL "user_id",
                        NULL "full_name",
                        NULL "username",
                        count(coalesce("assigned_to_id", -1)) "count",
                        NULL "photo",
                        NULL "email"
                   FROM "userstories_userstory"
             INNER JOIN "projects_project"
                     ON ("userstories_userstory"."project_id" = "projects_project"."id")
            INNER JOIN "projects_userstorystatus"
                ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
        LEFT OUTER JOIN "epics_relateduserstory"
                     ON ("userstories_userstory"."id" = "epics_relateduserstory"."user_story_id")
                  WHERE {where} AND "userstories_userstory"."id" NOT IN (
                    SELECT "userstories_userstory_assigned_users"."userstory_id" FROM
                      "userstories_userstory_assigned_users"
                      WHERE "userstories_userstory_assigned_users"."userstory_id" = "userstories_userstory"."id"
                  ) AND "userstories_userstory"."assigned_to_id" IS NULL
               GROUP BY "username";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count, photo, email in rows:
        result.append({
            "id": id,
            "full_name": full_name or username or "",
            "count": count,
            "photo": get_photo_url(photo),
            "big_photo": get_big_photo_url(photo),
            "gravatar_id": get_gravatar_id(email) if email else None
        })

        if id is None:
            none_valued_added = True

    # If there was no userstory with null assigned_to we manually add it
    if not none_valued_added:
        result.append({
            "id": None,
            "full_name": "",
            "count": 0,
            "photo": None,
            "big_photo": None,
            "gravatar_id": None
        })

    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
     WITH "us_counters" AS(
         SELECT DISTINCT "userstories_userstory"."owner_id" "owner_id",
                         "userstories_userstory"."id" "us_id"
                    FROM "userstories_userstory"
              INNER JOIN "projects_project"
                      ON ("userstories_userstory"."project_id" = "projects_project"."id")
                INNER JOIN "projects_userstorystatus"
                    ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
         LEFT OUTER JOIN "epics_relateduserstory"
                      ON ("userstories_userstory"."id" = "epics_relateduserstory"."user_story_id")
         LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                   WHERE {where}
            ),

            "counters" AS (
                 SELECT "owner_id",
                        COUNT("owner_id")
                   FROM "us_counters"
               GROUP BY "owner_id"
            )

                 SELECT "projects_membership"."user_id" "user_id",
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) "count",
                        "users_user"."photo" "photo",
                        "users_user"."email" "email"
                   FROM "projects_membership"
        LEFT OUTER JOIN "counters"
                     ON ("projects_membership"."user_id" = "counters"."owner_id")
             INNER JOIN "users_user"
                     ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- System users
                  UNION

                 SELECT "users_user"."id" "user_id",
                        "users_user"."full_name" "full_name",
                        "users_user"."username" "username",
                        COALESCE("counters"."count", 0) "count",
                        NULL "photo",
                        NULL "email"
                   FROM "users_user"
        LEFT OUTER JOIN "counters"
                     ON ("users_user"."id" = "counters"."owner_id")
                  WHERE ("users_user"."is_system" IS TRUE)
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, username, count, photo, email in rows:
        if count > 0:
            result.append({
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
                "photo": get_photo_url(photo),
                "big_photo": get_big_photo_url(photo),
                "gravatar_id": get_gravatar_id(email) if email else None
            })
    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_tags(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
           WITH "userstories_tags" AS (
                   SELECT "tag",
                          COUNT("tag") "counter"
                     FROM (
                      SELECT DISTINCT "userstories_userstory"."id" "us_id",
                                       UNNEST("userstories_userstory"."tags") "tag"
                                 FROM "userstories_userstory"
                        INNER JOIN "projects_project"
                            ON ("userstories_userstory"."project_id" = "projects_project"."id")
                        INNER JOIN "projects_userstorystatus"
                            ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
                        LEFT OUTER JOIN "epics_relateduserstory"
                            ON ("userstories_userstory"."id" = "epics_relateduserstory"."user_story_id")
                        LEFT OUTER JOIN "userstories_userstory_assigned_users"
                            ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                                WHERE {where}
                          ) "tags"
                    GROUP BY "tag"),

                "project_tags" AS (
                       SELECT reduce_dim("tags_colors") "tag_color"
                         FROM "projects_project"
                        WHERE "id"=%s)

         SELECT "tag_color"[1] "tag",
                "tag_color"[2] "color",
                COALESCE("userstories_tags"."counter", 0) "counter"
           FROM "project_tags"
LEFT OUTER JOIN "userstories_tags"
             ON "project_tags"."tag_color"[1] = "userstories_tags"."tag"
       ORDER BY "tag"
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for name, color, count in rows:
        result.append({
            "name": name,
            "color": color,
            "count": count,
        })
    return sorted(result, key=itemgetter("name"))


def _get_userstories_epics(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]
    extra_sql = """
       WITH "counters" AS (
               SELECT "epics_relateduserstory"."epic_id" AS "epic_id",
                      count("epics_relateduserstory"."id") AS "counter"
                 FROM "epics_relateduserstory"
           INNER JOIN "userstories_userstory"
                   ON ("userstories_userstory"."id" = "epics_relateduserstory"."user_story_id")
           INNER JOIN "projects_project"
                   ON ("userstories_userstory"."project_id" = "projects_project"."id")
            INNER JOIN "projects_userstorystatus"
                    ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
            LEFT OUTER JOIN "userstories_userstory_assigned_users"
                ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                WHERE {where}
             GROUP BY "epics_relateduserstory"."epic_id"
       )

         -- User stories with no epics (return results only if there are userstories)
               SELECT NULL AS "id",
                      NULL AS "ref",
                      NULL AS "subject",
                      0 AS "order",
                      count(COALESCE("epics_relateduserstory"."epic_id", -1)) AS "counter"
                 FROM "userstories_userstory"
      LEFT OUTER JOIN "epics_relateduserstory"
                   ON ("epics_relateduserstory"."user_story_id" = "userstories_userstory"."id")
           INNER JOIN "projects_project"
                   ON ("userstories_userstory"."project_id" = "projects_project"."id")
            INNER JOIN "projects_userstorystatus"
                ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
         LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory"."id" = "userstories_userstory_assigned_users"."userstory_id"
                WHERE {where} AND "epics_relateduserstory"."epic_id" IS NULL
             GROUP BY "epics_relateduserstory"."epic_id"

                UNION

               SELECT "epics_epic"."id" AS "id",
                      "epics_epic"."ref" AS "ref",
                      "epics_epic"."subject" AS "subject",
                      "epics_epic"."epics_order" AS "order",
                      COALESCE("counters"."counter", 0) AS "counter"
                 FROM "epics_epic"
      LEFT OUTER JOIN "counters"
                   ON ("counters"."epic_id" = "epics_epic"."id")
                WHERE "epics_epic"."project_id" = %s
        """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, ref, subject, order, count in rows:
        result.append({
            "id": id,
            "ref": ref,
            "subject": subject,
            "order": order,
            "count": count,
        })

    result = sorted(result, key=lambda k: (k["order"], k["id"] or 0))

    # Add row when there is no user stories with no epics
    if result == [] or result[0]["id"] is not None:
        result.insert(0, {
            "id": None,
            "ref": None,
            "subject": None,
            "order": 0,
            "count": 0,
        })
    return result


def _get_userstories_roles(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
     WITH "us_counters" AS (
         SELECT DISTINCT "userstories_userstory"."status_id" "status_id",
                         "userstories_userstory"."id" "us_id",
                         "projects_membership"."role_id" "role_id"
                    FROM "userstories_userstory"
              INNER JOIN "projects_project"
                      ON ("userstories_userstory"."project_id" = "projects_project"."id")
            INNER JOIN "projects_userstorystatus"
                ON ("userstories_userstory"."status_id" = "projects_userstorystatus"."id")
         LEFT OUTER JOIN "epics_relateduserstory"
                      ON "userstories_userstory"."id" = "epics_relateduserstory"."user_story_id"
         LEFT OUTER JOIN "userstories_userstory_assigned_users"
                      ON "userstories_userstory_assigned_users"."userstory_id" = "userstories_userstory"."id"
         LEFT OUTER JOIN "projects_membership"
                      ON "projects_membership"."user_id" = "userstories_userstory"."assigned_to_id"
                      OR "projects_membership"."user_id" = "userstories_userstory_assigned_users"."user_id"
                   WHERE {where}
            ),
             "counters" AS (
                  SELECT "role_id" as "role_id",
                         COUNT("role_id") "count"
                    FROM "us_counters"
                GROUP BY "role_id"
            )

                 SELECT "users_role"."id",
                        "users_role"."name",
                        "users_role"."order",
                        COALESCE("counters"."count", 0)
                   FROM "users_role"
        LEFT OUTER JOIN "counters"
                     ON "counters"."role_id" = "users_role"."id"
                  WHERE "users_role"."project_id" = %s
               ORDER BY "users_role"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": None,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def get_userstories_filters_data(project, querysets):
    """
    Given a project and an userstories queryset, return a simple data structure
    of all possible filters for the userstories in the queryset.
    """
    data = OrderedDict([
        ("statuses", _get_userstories_statuses(project, querysets["statuses"])),
        ("assigned_to",
         _get_userstories_assigned_to(project, querysets["assigned_to"])),
        ("assigned_users",
         _get_userstories_assigned_users(project, querysets["assigned_users"])),
        ("owners", _get_userstories_owners(project, querysets["owners"])),
        ("tags", _get_userstories_tags(project, querysets["tags"])),
        ("epics", _get_userstories_epics(project, querysets["epics"])),
        ("roles", _get_userstories_roles(project, querysets["roles"])),
    ])

    return data
