# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.projects.attachments.utils import attach_basic_attachments
from taiga.projects.attachments.utils import attach_total_attachments
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset
from taiga.projects.history.utils import attach_total_comments_to_queryset
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.votes.utils import attach_is_voter_to_queryset


def attach_total_points(queryset, as_field="total_points_attr"):
    """Attach total of point values to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the points as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT SUM(projects_points.value)
                    FROM userstories_rolepoints
                    INNER JOIN projects_points ON userstories_rolepoints.points_id = projects_points.id
                    WHERE userstories_rolepoints.user_story_id = {tbl}.id"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_role_points(queryset, as_field="role_points_attr"):
    """Attach role point as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the role points as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT FORMAT('{{%%s}}',
                           STRING_AGG(format(
                                '"%%s":%%s',
                                TO_JSON(userstories_rolepoints.role_id),
                                TO_JSON(userstories_rolepoints.points_id)
                            ), ',')
                          )::json
                    FROM userstories_rolepoints
                    WHERE userstories_rolepoints.user_story_id = {tbl}.id"""
    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_tasks(queryset, as_field="tasks_attr"):
    """Attach tasks as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach tasks as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    sql = """SELECT json_agg(row_to_json(t))
                FROM(
                    SELECT
                        tasks_task.id,
                        tasks_task.ref,
                        tasks_task.subject,
                        tasks_task.status_id,
                        tasks_task.is_blocked,
                        tasks_task.is_iocaine,
                        projects_taskstatus.is_closed
                FROM tasks_task
                INNER JOIN projects_taskstatus on projects_taskstatus.id = tasks_task.status_id
                WHERE user_story_id = {tbl}.id
                ORDER BY tasks_task.us_order, tasks_task.ref
                ) t
                """

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_epics(queryset, as_field="epics_attr"):
    """Attach epics as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the epics as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    sql = """SELECT json_agg(row_to_json(t))
               FROM (SELECT "epics_epic"."id" AS "id",
                            "epics_epic"."ref" AS "ref",
                            "epics_epic"."subject" AS "subject",
                            "epics_epic"."color" AS "color",
                            (SELECT row_to_json(p)
                              FROM (SELECT "projects_project"."id"    AS "id",
                                           "projects_project"."name"  AS "name",
                                           "projects_project"."slug"  AS "slug"
                                   ) p
                            ) AS "project"
                       FROM "epics_relateduserstory"
                 INNER JOIN "epics_epic" ON "epics_epic"."id" = "epics_relateduserstory"."epic_id"
                 INNER JOIN "projects_project" ON "projects_project"."id" = "epics_epic"."project_id"
                      WHERE "epics_relateduserstory"."user_story_id" = {tbl}.id
                   ORDER BY "projects_project"."name", "epics_epic"."ref") t"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_epic_order(queryset, epic_id, as_field="epic_order"):
    """Attach epic_order column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param epic_id: Order related to this epic.
    :param as_field: Attach order as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    sql = """SELECT "epics_relateduserstory"."order" AS "epic_order"
               FROM "epics_relateduserstory"
              WHERE "epics_relateduserstory"."user_story_id" = {tbl}.id and
                    "epics_relateduserstory"."epic_id" = {epic_id}"""

    sql = sql.format(tbl=model._meta.db_table, epic_id=int(epic_id))
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_extra_info(queryset, user=None, include_attachments=False, include_tasks=False, epic_id=None):
    queryset = attach_total_points(queryset)
    queryset = attach_role_points(queryset)
    queryset = attach_epics(queryset)

    if include_attachments:
        queryset = attach_basic_attachments(queryset)
        queryset = queryset.extra(select={"include_attachments": "True"})

    if include_tasks:
        queryset = attach_tasks(queryset)
        queryset = queryset.extra(select={"include_tasks": "True"})

    if epic_id is not None:
        queryset = attach_epic_order(queryset, epic_id)
        queryset = queryset.extra(select={"include_epic_order": "True"})

    queryset = attach_total_attachments(queryset)
    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_voter_to_queryset(queryset, user)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    queryset = attach_total_comments_to_queryset(queryset)
    return queryset


def attach_assigned_users(queryset, as_field="assigned_users_attr"):
    """Attach assigned users as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach assigned as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    sql = """SELECT "userstories_userstory_assigned_users"."user_id" AS "user_id"
                FROM "userstories_userstory_assigned_users"
                WHERE "userstories_userstory_assigned_users"."userstory_id" = {tbl}.id"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset
