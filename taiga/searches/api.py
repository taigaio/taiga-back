# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from taiga.base.api import viewsets

from taiga.base import response
from taiga.base.api.utils import get_object_or_404
from taiga.permissions.service import user_has_perm

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
        return get_object_or_404(project_model, pk=project_id)

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
