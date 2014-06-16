# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.db.models.loading import get_model

from rest_framework.response import Response
from rest_framework import viewsets

from taiga.base import exceptions as excp
from taiga.projects.userstories.serializers import UserStorySerializer
from taiga.projects.tasks.serializers import TaskSerializer
from taiga.projects.issues.serializers import IssueSerializer
from taiga.projects.wiki.serializers import WikiPageSerializer

from . import services


class SearchViewSet(viewsets.ViewSet):
    def list(self, request, **kwargs):
        project_model = get_model("projects", "Project")

        text = request.QUERY_PARAMS.get('text', "")
        project_id = request.QUERY_PARAMS.get('project', None)

        try:
            project = self._get_project(project_id)
        except (project_model.DoesNotExist, TypeError):
            raise excp.PermissionDenied({"detail": "Wrong project id"})

        result = {
            "userstories": self._search_user_stories(project, text),
            "tasks": self._search_tasks(project, text),
            "issues": self._search_issues(project, text),
            "wikipages": self._search_wiki_pages(project, text)
        }

        result["count"] = sum(map(lambda x: len(x), result.values()))
        return Response(result)

    def _get_project(self, project_id):
        project_model = get_model("projects", "Project")
        own_projects = (project_model.objects
                            .filter(members=self.request.user))

        return own_projects.get(pk=project_id)

    def _search_user_stories(self, project, text):
        queryset = services.search_user_stories(project, text)
        serializer = UserStorySerializer(queryset, many=True)
        return serializer.data

    def _search_tasks(self, project, text):
        queryset = services.search_tasks(project, text)
        serializer = TaskSerializer(queryset, many=True)
        return serializer.data

    def _search_issues(self, project, text):
        queryset = services.search_issues(project, text)
        serializer = IssueSerializer(queryset, many=True)
        return serializer.data

    def _search_wiki_pages(self, project, text):
        queryset = services.search_wiki_pages(project, text)
        serializer = WikiPageSerializer(queryset, many=True)
        return serializer.data
