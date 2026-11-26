# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps

from taiga.base.api import viewsets

from taiga.base import response
from taiga.base.api.utils import get_object_or_error
from taiga.permissions.services import user_has_perm

from . import services
from . import serializers


from concurrent import futures


class SearchPlanEntry:
    def __init__(self, permission, result_key, search_fn):
        self.permission = permission
        self.result_key = result_key
        self.search_fn = search_fn

    def is_authorized(self, user, project):
        return user_has_perm(user, self.permission, project)

    def run(self, pool, project, user, query_text):
        future = pool.submit(self.search_fn, project, query_text)
        future.result_key = self.result_key
        return future


class SearchTaskExecutor:
    def __init__(self, pool, project, user, query_text, search_plan):
        self.pool = pool
        self.project = project
        self.user = user
        self.query_text = query_text
        self.search_plan = search_plan

    def build_search_futures(self):
        futures_list = []
        for entry in self.search_plan:
            if entry.is_authorized(self.user, self.project):
                futures_list.append(entry.run(self.pool, self.project, self.user, self.query_text))
        return futures_list

    def collect_results(self, futures_list):
        results = {}
        for future in futures.as_completed(futures_list):
            data = []
            try:
                data = future.result()
            except Exception as exc:
                print('%s generated an exception: %s' % (future.result_key, exc))
            finally:
                results[future.result_key] = data
        return results

class SearchViewSet(viewsets.ViewSet):
    def list(self, request, **kwargs):
        query_text = request.QUERY_PARAMS.get('text', "")
        project_id = request.QUERY_PARAMS.get('project', None)

        project = self._get_project(project_id)

        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            search_plan = [
                SearchPlanEntry("view_epics", "epics", self._search_epics),
                SearchPlanEntry("view_us", "userstories", self._search_project_user_stories),
                SearchPlanEntry("view_tasks", "tasks", self._search_project_tasks),
                SearchPlanEntry("view_issues", "issues", self._search_issues),
                SearchPlanEntry("view_wiki_pages", "wikipages", self._search_wiki_pages),
            ]
            task_executor = SearchTaskExecutor(executor, project, request.user, query_text, search_plan)
            search_futures = task_executor.build_search_futures()
            aggregated_results = task_executor.collect_results(search_futures)

        aggregated_results["count"] = sum(map(lambda x: len(x), aggregated_results.values()))
        return response.Ok(aggregated_results)

    def _get_project(self, project_id):
        project_model = apps.get_model("projects", "Project")
        return get_object_or_error(project_model, self.request.user, pk=project_id)

    def _search_epics(self, project, text):
        queryset = services.search_epics(project, text)
        serializer = serializers.EpicSearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_project_user_stories(self, project, text):
        queryset = services.search_user_stories(project, text)
        serializer = serializers.UserStorySearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_project_tasks(self, project, text):
        queryset = services.search_tasks(project, text)
        serializer = serializers.TaskSearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_issues(self, project, text):
        queryset = services.search_issues(project, text)
        serializer = serializers.IssueSearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_wiki_pages(self, project, text):
        queryset = services.search_wiki_pages(project, text)
        serializer = serializers.WikiPageSearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _build_search_futures(self, executor, project, user, query_text):
        search_plan = [
            SearchPlanEntry("view_epics", "epics", self._search_epics),
            SearchPlanEntry("view_us", "userstories", self._search_project_user_stories),
            SearchPlanEntry("view_tasks", "tasks", self._search_project_tasks),
            SearchPlanEntry("view_issues", "issues", self._search_issues),
            SearchPlanEntry("view_wiki_pages", "wikipages", self._search_wiki_pages),
        ]
        return SearchTaskExecutor(executor, project, user, query_text, search_plan).build_search_futures()

    def _collect_results(self, futures_list):
        return SearchTaskExecutor(None, None, None, None, []).collect_results(futures_list)
