# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
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
