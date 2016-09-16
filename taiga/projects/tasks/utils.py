# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from taiga.projects.attachments.utils import attach_basic_attachments
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.votes.utils import attach_is_voter_to_queryset


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


def attach_extra_info(queryset, user=None, include_attachments=False):
    if include_attachments:
        queryset = attach_basic_attachments(queryset)
        queryset = queryset.extra(select={"include_attachments": "True"})

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_voter_to_queryset(queryset, user)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    queryset = attach_user_story_extra_info(queryset)
    return queryset
