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

class SearchViewSet(viewsets.ViewSet):
    def list(self, request, **kwargs):
        text = request.QUERY_PARAMS.get('text', "")
        project_id = request.QUERY_PARAMS.get('project', None)

        project = self._get_project(project_id)

        result = {}
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures_list = []
            if user_has_perm(request.user, "view_epics", project):
                epics_future = executor.submit(self._search_epics, project, text)
                epics_future.result_key = "epics"
                futures_list.append(epics_future)
            if user_has_perm(request.user, "view_us", project):
                uss_future = executor.submit(self._search_user_stories, project, text)
                uss_future.result_key = "userstories"
                futures_list.append(uss_future)
            if user_has_perm(request.user, "view_tasks", project):
                tasks_future = executor.submit(self._search_tasks, project, text)
                tasks_future.result_key = "tasks"
                futures_list.append(tasks_future)
            if user_has_perm(request.user, "view_issues", project):
                issues_future = executor.submit(self._search_issues, project, text)
                issues_future.result_key = "issues"
                futures_list.append(issues_future)
            if user_has_perm(request.user, "view_wiki_pages", project):
                wiki_pages_future = executor.submit(self._search_wiki_pages, project, text)
                wiki_pages_future.result_key = "wikipages"
                futures_list.append(wiki_pages_future)

            for future in futures.as_completed(futures_list):
                data = []
                try:
                    data = future.result()
                except Exception as exc:
                    print('%s generated an exception: %s' % (future.result_key, exc))
                finally:
                    result[future.result_key] = data

        result["count"] = sum(map(lambda x: len(x), result.values()))
        return response.Ok(result)

    def _get_project(self, project_id):
        project_model = apps.get_model("projects", "Project")
        return get_object_or_error(project_model, self.request.user, pk=project_id)

    def _search_epics(self, project, text):
        queryset = services.search_epics(project, text)
        serializer = serializers.EpicSearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_user_stories(self, project, text):
        queryset = services.search_user_stories(project, text)
        serializer = serializers.UserStorySearchResultsSerializer(queryset, many=True)
        return serializer.data

    def _search_tasks(self, project, text):
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
