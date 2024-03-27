# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
    tsquery = "to_tsquery('simple', %s)"
    tsvector = """
        setweight(to_tsvector('simple', coalesce(wiki_wikipage.slug)), 'A') ||
        setweight(to_tsvector('simple', coalesce(wiki_wikipage.content)), 'B')
    """

    return _search_by_query(queryset, tsquery, tsvector, text)


def _search_items(queryset, table, text):
    tsquery = "to_tsquery('simple', %s)"
    tsvector = """
        setweight(to_tsvector('simple',
                              coalesce({table}.subject) || ' ' ||
                              coalesce({table}.ref)), 'A') ||
        setweight(to_tsvector('simple', coalesce(inmutable_array_to_string({table}.tags))), 'B') ||
        setweight(to_tsvector('simple', coalesce({table}.description)), 'C')
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
