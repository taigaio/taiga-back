# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from typing import List, Optional

import csv
import io
import re
import json
import logging
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
from taiga.doubai_ai import ask_once

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
    return [
        models.UserStory(subject=line, **additional_fields)
        for line in text.split_in_lines(bulk_data)
    ]


def create_userstories_in_bulk(
    bulk_data, callback=None, precall=None, **additional_fields
):
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


def update_userstories_order_in_bulk(
    bulk_data: list,
    field: str,
    project: object,
    status: object = None,
    milestone: object = None,
):
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
    events.emit_event_for_ids(
        ids=user_story_ids, content_type="userstories.userstory", projectid=project.pk
    )
    db.update_attr_in_bulk_for_ids(us_orders, field, models.UserStory)
    return us_orders


def reset_userstories_kanban_order_in_bulk(
    project: Project, bulk_userstories: List[int]
):
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
    events.emit_event_for_ids(
        ids=bulk_userstories, content_type="userstories.userstory", projectid=project.id
    )


def update_userstories_backlog_or_sprint_order_in_bulk(
    user: User,
    project: Project,
    bulk_userstories: List[int],
    before_userstory: Optional[models.UserStory] = None,
    after_userstory: Optional[models.UserStory] = None,
    milestone: Optional[Milestone] = None,
):
    """
    Updates the order of the userstories specified adding the extra updates
    needed to keep consistency.

    Note: `after_userstory_id` and `before_userstory_id` are mutually exclusive;
          you can use only one at a given request. They can be both None which
          means "at the beginning of is cell"

     - `bulk_userstories` should be a list of user stories IDs
    """
    # Get ids from milestones affected
    milestones_ids = set(
        project.milestones.filter(user_stories__in=bulk_userstories).values_list(
            "id", flat=True
        )
    )
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
        user_stories = user_stories.filter(
            **{f"{order_param}__gte": getattr(before_userstory, order_param)}
        )
    # if after_userstory, exclude it and get only elements after it:
    elif after_userstory:
        user_stories = user_stories.exclude(id=after_userstory.id).filter(
            **{f"{order_param}__gte": getattr(after_userstory, order_param)}
        )

    # sort and get only ids
    user_story_ids = user_stories.order_by(order_param, "id").values_list(
        "id", flat=True
    )

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

    data = tuple(zip(user_story_ids, user_story_orders))

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
        _async_tasks_after_backlog_or_sprint_order_change.delay(
            bulk_userstories, milestones_ids, user.id
        )
    else:
        _async_tasks_after_backlog_or_sprint_order_change(
            bulk_userstories, milestones_ids, user.id
        )

    # Sent events of updated stories
    events.emit_event_for_ids(
        ids=user_story_ids, content_type="userstories.userstory", projectid=project.pk
    )

    # Generate response with modified info
    res = (
        {"id": id, "milestone": milestone.id if milestone else None, order_param: order}
        for (id, order) in data
    )
    return res


@app.task
def _async_tasks_after_backlog_or_sprint_order_change(
    userstories_ids, milestones_ids, user_id
):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    # Take snapshots for user stories and their taks
    for userstory in models.UserStory.objects.filter(id__in=userstories_ids):
        take_snapshot(userstory, user=user)

        for task in userstory.tasks.all():
            take_snapshot(task, user=user)

    # Check if milestones are open or closed after stories are moved
    for milestone in Milestone.objects.filter(id__in=milestones_ids):
        _recalculate_is_closed_for_milestone(milestone)


def update_userstories_kanban_order_in_bulk(
    user: User,
    project: Project,
    status: UserStoryStatus,
    bulk_userstories: List[int],
    before_userstory: Optional[models.UserStory] = None,
    after_userstory: Optional[models.UserStory] = None,
    swimlane: Optional[Swimlane] = None,
):
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
        user_stories = user_stories.filter(
            kanban_order__gte=before_userstory.kanban_order
        )
    # if after_userstory, exclude it and get only elements after it:
    elif after_userstory:
        user_stories = user_stories.exclude(id=after_userstory.id).filter(
            kanban_order__gte=after_userstory.kanban_order
        )

    # sort and get only ids
    user_story_ids = user_stories.order_by("kanban_order", "id").values_list(
        "id", flat=True
    )

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

    data = tuple(zip(user_story_ids, user_story_kanban_orders))

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
    events.emit_event_for_ids(
        ids=user_story_ids, content_type="userstories.userstory", projectid=project.pk
    )

    # Generate response with modified info
    res = (
        {
            "id": id,
            "swimlane": swimlane.id if swimlane else None,
            "status": status.id,
            "kanban_order": kanban_order,
        }
        for (id, kanban_order) in data
    )
    return res


@app.task
def _async_tasks_after_kanban_order_change(userstories_ids, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    for userstory in models.UserStory.objects.filter(id__in=userstories_ids):
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

    events.emit_event_for_ids(
        ids=user_story_ids,
        content_type="userstories.userstory",
        projectid=milestone.project.pk,
    )

    db.update_attr_in_bulk_for_ids(
        us_milestones, "milestone_id", model=models.UserStory
    )
    db.update_attr_in_bulk_for_ids(us_orders, "sprint_order", models.UserStory)

    # Updating the milestone for the tasks
    Task.objects.filter(user_story_id__in=[e["us_id"] for e in bulk_data]).update(
        milestone=milestone
    )

    return us_orders


def snapshot_userstories_in_bulk(bulk_data, user):
    for us_data in bulk_data:
        try:
            us = models.UserStory.objects.get(pk=us_data["us_id"])
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

    if all(
        [
            task.status is not None and task.status.is_closed
            for task in user_story.tasks.all()
        ]
    ):
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
    fieldnames = [
        "id",
        "ref",
        "subject",
        "description",
        "sprint_id",
        "sprint",
        "sprint_estimated_start",
        "sprint_estimated_finish",
        "owner",
        "owner_full_name",
        "assigned_to",
        "assigned_to_full_name",
        "assigned_users",
        "assigned_users_full_name",
        "status",
        "is_closed",
        "swimlane",
    ]

    roles = project.roles.filter(computable=True).order_by("slug")
    for role in roles:
        fieldnames.append("{}-points".format(role.slug))

    fieldnames.append("total-points")

    fieldnames += [
        "backlog_order",
        "sprint_order",
        "kanban_order",
        "created_date",
        "modified_date",
        "finish_date",
        "client_requirement",
        "team_requirement",
        "attachments",
        "generated_from_issue",
        "generated_from_task",
        "from_task_ref",
        "external_reference",
        "tasks",
        "tags",
        "watchers",
        "voters",
        "due_date",
        "due_date_reason",
        "epics",
    ]

    custom_attrs = project.userstorycustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related(
        "role_points",
        "role_points__points",
        "role_points__role",
        "tasks",
        "epics",
        "attachments",
        "custom_attributes_values",
    )
    queryset = queryset.select_related(
        "milestone",
        "project",
        "status",
        "owner",
        "assigned_to",
        "generated_from_issue",
        "generated_from_task",
    )

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for us in queryset:
        row = {
            "id": us.id,
            "ref": us.ref,
            "subject": text.sanitize_csv_text_value(us.subject),
            "description": text.sanitize_csv_text_value(us.description),
            "sprint_id": us.milestone.id if us.milestone else None,
            "sprint": (
                text.sanitize_csv_text_value(us.milestone.name)
                if us.milestone
                else None
            ),
            "sprint_estimated_start": (
                us.milestone.estimated_start if us.milestone else None
            ),
            "sprint_estimated_finish": (
                us.milestone.estimated_finish if us.milestone else None
            ),
            "owner": us.owner.username if us.owner else None,
            "owner_full_name": (
                text.sanitize_csv_text_value(us.owner.get_full_name())
                if us.owner
                else None
            ),
            "assigned_to": us.assigned_to.username if us.assigned_to else None,
            "assigned_to_full_name": (
                text.sanitize_csv_text_value(us.assigned_to.get_full_name())
                if us.assigned_to
                else None
            ),
            "assigned_users": ",".join(
                [assigned_user.username for assigned_user in us.assigned_users.all()]
            ),
            "assigned_users_full_name": text.sanitize_csv_text_value(
                ",".join(
                    [
                        assigned_user.get_full_name()
                        for assigned_user in us.assigned_users.all()
                    ]
                )
            ),
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
            "generated_from_issue": (
                us.generated_from_issue.ref if us.generated_from_issue else None
            ),
            "generated_from_task": (
                us.generated_from_task.ref if us.generated_from_task else None
            ),
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

        us_role_points_by_role_id = {
            us_rp.role.id: us_rp.points.value for us_rp in us.role_points.all()
        }
        for role in roles:
            row["{}-points".format(role.slug)] = us_role_points_by_role_id.get(
                role.id, 0
            )

        row["total-points"] = us.get_total_points()

        for custom_attr in custom_attrs:
            if not hasattr(us, "custom_attributes_values"):
                continue
            value = us.custom_attributes_values.attributes_values.get(
                str(custom_attr.id), None
            )
            row[custom_attr.name] = text.sanitize_csv_text_value(value)

        writer.writerow(row)

    return csv_data


#####################################################
# Api filter data
#####################################################


def _get_userstories_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": color,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_userstories_assigned_to(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count in rows:
        result.append(
            {
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
            }
        )

        if id is None:
            none_valued_added = True

    # If there was no userstory with null assigned_to we manually add it
    if not none_valued_added:
        result.append(
            {
                "id": None,
                "full_name": "",
                "count": 0,
            }
        )

    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_assigned_users(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count, photo, email in rows:
        result.append(
            {
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
                "photo": get_photo_url(photo),
                "big_photo": get_big_photo_url(photo),
                "gravatar_id": get_gravatar_id(email) if email else None,
            }
        )

        if id is None:
            none_valued_added = True

    # If there was no userstory with null assigned_to we manually add it
    if not none_valued_added:
        result.append(
            {
                "id": None,
                "full_name": "",
                "count": 0,
                "photo": None,
                "big_photo": None,
                "gravatar_id": None,
            }
        )

    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, username, count, photo, email in rows:
        if count > 0:
            result.append(
                {
                    "id": id,
                    "full_name": full_name or username or "",
                    "count": count,
                    "photo": get_photo_url(photo),
                    "big_photo": get_big_photo_url(photo),
                    "gravatar_id": get_gravatar_id(email) if email else None,
                }
            )
    return sorted(result, key=itemgetter("full_name"))


def _get_userstories_tags(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for name, color, count in rows:
        result.append(
            {
                "name": name,
                "color": color,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("name"))


def _get_userstories_epics(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
        """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, ref, subject, order, count in rows:
        result.append(
            {
                "id": id,
                "ref": ref,
                "subject": subject,
                "order": order,
                "count": count,
            }
        )

    result = sorted(result, key=lambda k: (k["order"], k["id"] or 0))

    # Add row when there is no user stories with no epics
    if result == [] or result[0]["id"] is not None:
        result.insert(
            0,
            {
                "id": None,
                "ref": None,
                "subject": None,
                "order": 0,
                "count": 0,
            },
        )
    return result


def _get_userstories_roles(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": None,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def get_userstories_filters_data(project, querysets):
    """
    Given a project and an userstories queryset, return a simple data structure
    of all possible filters for the userstories in the queryset.
    """
    data = OrderedDict(
        [
            ("statuses", _get_userstories_statuses(project, querysets["statuses"])),
            (
                "assigned_to",
                _get_userstories_assigned_to(project, querysets["assigned_to"]),
            ),
            (
                "assigned_users",
                _get_userstories_assigned_users(project, querysets["assigned_users"]),
            ),
            ("owners", _get_userstories_owners(project, querysets["owners"])),
            ("tags", _get_userstories_tags(project, querysets["tags"])),
            ("epics", _get_userstories_epics(project, querysets["epics"])),
            ("roles", _get_userstories_roles(project, querysets["roles"])),
        ]
    )

    return data

# 假设 ask_once 函数和 logging, re, json 模块已正确导入和配置
# 为了让代码可运行和演示，我们依然使用模拟的 ask_once

logger = logging.getLogger(__name__)

# --- 核心异常类（保持不变）---

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass

# --- 核心故事生成函数（函数名和返回格式变更）---

def generate_single_story(requirement_text: str):
    """
    Generates a structured AI suggestion (Subject, Description, Tags) from a
    single piece of natural language text for frontend consumption.
    It applies cleaning and anonymization before building the prompt.

    Args:
        requirement_text (str): The raw natural language description of the requirement.

    Returns:
        dict: The generated suggestion structure (suggestion_subject, 
              suggestion_description, suggestion_tags).
              Raises AIServiceError on failure.
    """
    processed_text = "" # 确保在 try 块外初始化
    try:
        # 0. 预处理：清洁并保护输入数据
        processed_text = preprocess(requirement_text)
            
        # 1. 构建 Prompt 和 Question (已修改，要求新格式)
        system_prompt = "You are a product owner specializing in Agile user story creation. Your response must be a valid JSON object."
        question = build_suggestion_prompt(processed_text) # 变动点 1: 调用新的 prompt 函数
            
        # 2. 调用 ask_once 函数 (替换为实际的 AI 调用)
        # 假设 ai_text_response = ask_once(question=question, prompt=system_prompt)
        # 为了演示，我们使用一个模拟的响应：
        # 注意: 在实际运行中，您需要确保您的 ask_once 函数返回的是符合新格式的文本。
        # 暂时使用一个模拟调用：
        ai_text_response = ask_once(question=question, prompt=system_prompt)
            
        # 3. 解析返回的文本 (已修改，解析新格式)
        suggestion_data = parse_ai_response(ai_text_response)

        # 检查解析结果是否是默认的失败结构
        # 变动点 2: 检查的键名已更改
        if suggestion_data.get("suggestion_subject") == get_default_story().get("suggestion_subject"):
            raise ValueError("AI response failed to parse and returned a default structure.")
                
        return suggestion_data
            
    except Exception as e:
        # 使用 processed_text 进行日志记录，避免记录原始敏感数据
        log_text = processed_text[:50] if processed_text else requirement_text[:50]
        logger.error(f"AI suggestion generation failed for processed requirement: '{log_text}...': {e}")
        # 变动点 3: 确保 raise AIServiceError 包装了原始错误
        raise AIServiceError(str(e))

# --- 预处理辅助方法（保持不变）---
def anonymize(text: str) -> str:
    """Anonymize sensitive data: email, phone, ID, bank card"""
    patterns = [
        # 1. 邮箱：最精确，冲突少
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
        
        # 2. 身份证：精确匹配 17 位数字 + 最后一位数字或 X/x
        (r"\d{17}[\dXx]", "[ID]"),
        
        # 3. 银行卡：匹配 12 到 19 位数字。由于身份证已处理，不会再误伤。
        # 注意：使用 \b 确保只匹配完整的数字串，避免匹配到句子中的普通数字。
        (r"\b\d{12,19}\b", "[BANKCARD]"),
        
        # 4. 手机：匹配 1[3-9]开头的11位数字。
        # 注意：使用 \b 确保是完整的 11 位数字。
        (r"\b1[3-9]\d{9}\b", "[PHONE]"),
    ]
    
    for pattern, repl in patterns:
        text = re.sub(pattern, repl, text)
        
    return text

def clean_text(text: str) -> str:
    """Basic cleaning: remove HTML, URLs, extra spaces"""
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 移除 URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)
    # 规范化空格：将多个空格替换为单个空格，并移除首尾空格
    text = re.sub(r"\s+", " ", text).strip()
    return text

def preprocess(text: str) -> str:
    """Full preprocessing pipeline: Anonymize -> Clean"""
    result = text
    # 1. 匿名化敏感信息
    result = anonymize(result)
    # 2. 基础文本清洁
    result = clean_text(result)
    return result
    
# --- 故事生成辅助方法（已修改）---

# 变动点 4: 更改函数名并调整 Prompt 内容以要求新的 JSON 结构
def build_suggestion_prompt(requirement_text):
    """Builds the prompt for the AI model based on natural language text, 
    requesting the specific frontend JSON structure."""
    return f"""Analyze the following natural language requirement and transform it
into a structured User Story in English.

Requirement Text:
"{requirement_text}"

Please provide the analysis result in a valid JSON format with the following fields:
1. 'suggestion_subject': A short, clear headline summarizing the story.
2. 'suggestion_description': The full user story text, strictly following the template:
   "As a <role>, I want <goal>, So that <value>".
3. 'suggestion_tags': An array of 3 to 5 JSON objects, where each object has a single field 'name'
   containing a relevant keyword or label (e.g., feature area, priority, user type).

Target JSON Format Example:
{{
  "suggestion_description": "...",
  "suggestion_subject": "...",
  "suggestion_tags": [
    {{ "name": "high priority" }},
    {{ "name": "..." }}
  ]
}}

IMPORTANT:
- Your entire response MUST be a single, valid JSON object.
- The 'suggestion_tags' array must contain between 3 and 5 tag objects.
- Do not include any text or formatting outside of the JSON object.
- The entire response should be in English."""


# 变动点 5: 更改 parse_ai_response 函数，使其可以处理目标 JSON 格式
def parse_ai_response(ai_text):
    """Parses the JSON response from the AI."""
    try:
        json_start = ai_text.find('{')
        json_end = ai_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in AI response")
            
        json_str = ai_text[json_start:json_end]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse AI response: {e}\nRaw: {ai_text[:100]}...")
        return get_default_story()

# 变动点 6: 更改 get_default_story 函数，返回目标 JSON 格式的默认结构
def get_default_story():
    """Returns a default user story object for fallback cases in the new format."""
    return {
        "suggestion_subject": "Default Suggestion (AI Failed)",
        "suggestion_description": "As a system administrator, I want to review this requirement, So that the correct user story can be created manually.",
        "suggestion_tags": [
            {"name": "manual-review"},
            {"name": "ai-failure"},
            {"name": "critical"}
        ]
    }