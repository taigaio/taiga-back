# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.projects.attachments.utils import attach_basic_attachments
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.votes.utils import attach_is_voter_to_queryset
from taiga.projects.history.utils import attach_total_comments_to_queryset


def attach_user_story_extra_info(queryset, as_field="user_story_extra_info"):
    """Attach userstory extra info  as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the userstory extra info as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    sql = """SELECT row_to_json(u)
               FROM (SELECT "userstories_userstory"."id" AS "id",
                            "userstories_userstory"."ref" AS "ref",
                            "userstories_userstory"."subject" AS "subject",
                            (SELECT json_agg(row_to_json(t))
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
                                 INNER JOIN "epics_epic"
                                         ON "epics_epic"."id" = "epics_relateduserstory"."epic_id"
                                 INNER JOIN "projects_project"
                                         ON "projects_project"."id" = "epics_epic"."project_id"
                                      WHERE "epics_relateduserstory"."user_story_id" = "{tbl}"."user_story_id"
                                   ORDER BY "projects_project"."name", "epics_epic"."ref") t) AS "epics"
               FROM "userstories_userstory"
              WHERE "userstories_userstory"."id" = "{tbl}"."user_story_id") u"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_generated_user_stories(queryset, as_field="generated_user_stories_attr"):
    """Attach generated user stories json column to each object of the queryset.

    :param queryset: A Django issues queryset object.
    :param as_field: Attach the generated user stories as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT json_agg(row_to_json(t))
                FROM(
                    SELECT
                        userstories_userstory.id,
                        userstories_userstory.ref,
                        userstories_userstory.subject
                FROM userstories_userstory
                WHERE generated_from_task_id = {tbl}.id) t"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_extra_info(queryset, user=None, include_attachments=False):
    if include_attachments:
        queryset = attach_basic_attachments(queryset)
        queryset = queryset.extra(select={"include_attachments": "True"})

    queryset = attach_generated_user_stories(queryset)
    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_voter_to_queryset(queryset, user)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    queryset = attach_user_story_extra_info(queryset)
    queryset = attach_total_comments_to_queryset(queryset)
    return queryset
