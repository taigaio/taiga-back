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


def attach_extra_info(queryset, user=None, include_attachments=False):
    if include_attachments:
        queryset = attach_basic_attachments(queryset)
        queryset = queryset.extra(select={"include_attachments": "True"})

    queryset = attach_user_stories_counts_to_queryset(queryset)
    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_voter_to_queryset(queryset, user)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    return queryset


def attach_user_stories_counts_to_queryset(queryset, as_field="user_stories_counts"):
    model = queryset.model
    sql = """
            SELECT json_build_object('total', count(t.*), 'progress', sum(t.percentaje_completed))
            FROM(
                SELECT
                    --userstories_userstory.id as userstories_userstory_id,
                    --userstories_userstory.is_closed as userstories_userstory_is_closed,
                    CASE WHEN userstories_userstory.is_closed
                         THEN 1
                         ELSE
                            COALESCE(COUNT(tasks_task.id) FILTER (WHERE projects_taskstatus.is_closed = TRUE)::real / NULLIF(COUNT(tasks_task.id), 0),0)--,
                    END AS percentaje_completed

                FROM epics_relateduserstory
                INNER JOIN userstories_userstory ON epics_relateduserstory.user_story_id = userstories_userstory.id
                LEFT JOIN tasks_task ON tasks_task.user_story_id = userstories_userstory.id
                LEFT JOIN projects_taskstatus ON tasks_task.status_id = projects_taskstatus.id
                     WHERE epics_relateduserstory.epic_id = {tbl}.id
                     GROUP BY userstories_userstory.id) t"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset
