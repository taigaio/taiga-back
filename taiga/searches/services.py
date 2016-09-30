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

from django.apps import apps
from django.conf import settings
from taiga.base.utils.db import to_tsquery
from taiga.projects.userstories.utils import attach_total_points

MAX_RESULTS = getattr(settings, "SEARCHES_MAX_RESULTS", 150)


def search_epics(project, text):
    model = apps.get_model("epics", "Epic")
    queryset = model.objects.filter(project_id=project.pk)
    table = "epics_epic"
    return _search_items(queryset, table, text)


def search_user_stories(project, text):
    model = apps.get_model("userstories", "UserStory")
    queryset = model.objects.filter(project_id=project.pk)
    table = "userstories_userstory"
    return _search_items(queryset, table, text)


def search_tasks(project, text):
    model = apps.get_model("tasks", "Task")
    queryset = model.objects.filter(project_id=project.pk)
    table = "tasks_task"
    return _search_items(queryset, table, text)


def search_issues(project, text):
    model = apps.get_model("issues", "Issue")
    queryset = model.objects.filter(project_id=project.pk)
    table = "issues_issue"
    return _search_items(queryset, table, text)


def search_wiki_pages(project, text):
    model = apps.get_model("wiki", "WikiPage")
    queryset = model.objects.filter(project_id=project.pk)
    tsquery = "to_tsquery('english_nostop', %s)"
    tsvector = """
        setweight(to_tsvector('english_nostop', coalesce(wiki_wikipage.slug)), 'A') ||
        setweight(to_tsvector('english_nostop', coalesce(wiki_wikipage.content)), 'B')
    """

    return _search_by_query(queryset, tsquery, tsvector, text)


def _search_items(queryset, table, text):
    tsquery = "to_tsquery('english_nostop', %s)"
    tsvector = """
        setweight(to_tsvector('english_nostop',
                              coalesce({table}.subject) || ' ' ||
                              coalesce({table}.ref)), 'A') ||
        setweight(to_tsvector('english_nostop', coalesce(inmutable_array_to_string({table}.tags))), 'B') ||
        setweight(to_tsvector('english_nostop', coalesce({table}.description)), 'C')
    """.format(table=table)
    return _search_by_query(queryset, tsquery, tsvector, text)


def _search_by_query(queryset, tsquery, tsvector, text):
    select = {
        "rank": "ts_rank({tsvector},{tsquery})".format(tsquery=tsquery,
                                                       tsvector=tsvector),
    }
    order_by = ["-rank", ]
    where = ["{tsvector} @@ {tsquery}".format(tsquery=tsquery,
                                              tsvector=tsvector), ]

    if text:
        queryset = queryset.extra(select=select,
                                  select_params=[to_tsquery(text)],
                                  where=where,
                                  params=[to_tsquery(text)],
                                  order_by=order_by)

    queryset = attach_total_points(queryset)
    return queryset[:MAX_RESULTS]
