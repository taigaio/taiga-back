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


class SearchViewSet(viewsets.ViewSet):
    def list(self, request, **kwargs):
        project_model = get_model("projects", "Project")
        text = request.QUERY_PARAMS.get('text', "")
        get_all = request.QUERY_PARAMS.get('get_all', False)
        project_id = request.QUERY_PARAMS.get('project', None)

        try:
            project = self._get_project(project_id)
        except (project_model.DoesNotExist, TypeError):
            raise excp.PermissionDenied({"detail": "Wrong project id"})

        result = {
            "userstories": self._search_user_stories(project, text, get_all),
            "tasks": self._search_tasks(project, text, get_all),
            "issues": self._search_issues(project, text, get_all),
            "wikipages": self._search_wiki_pages(project, text, get_all)
        }

        result["count"] = sum(map(lambda x: len(x), result.values()))
        return Response(result)

    def _get_project(self, project_id):
        project_model = get_model("projects", "Project")
        own_projects = (project_model.objects
                            .filter(members=self.request.user))

        return own_projects.get(pk=project_id)

    def _search_user_stories(self, project, text, get_all):
        where_clause = ("to_tsvector(userstories_userstory.subject || "
                        "userstories_userstory.description) @@ plainto_tsquery(%s)")

        model_cls = get_model("userstories", "UserStory")
        if get_all != "false" and text == '':
            queryset = model_cls.objects.filter(project_id=project.pk)
        else:
            queryset = (model_cls.objects
                            .extra(where=[where_clause], params=[text])
                            .filter(project_id=project.pk)[:50])

        serializer = UserStorySerializer(queryset, many=True)
        return serializer.data

    def _search_tasks(self, project, text, get_all):
        where_clause = ("to_tsvector(tasks_task.subject || tasks_task.description) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("tasks", "Task")
        if get_all != "false" and text == '':
            queryset = model_cls.objects.filter(project_id=project.pk)
        else:
            queryset = (model_cls.objects
                            .extra(where=[where_clause], params=[text])
                            .filter(project_id=project.pk)[:50])

        serializer = TaskSerializer(queryset, many=True)
        return serializer.data

    def _search_issues(self, project, text, get_all):
        where_clause = ("to_tsvector(issues_issue.subject || issues_issue.description) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("issues", "Issue")
        if get_all != "false" and text == '':
            queryset = model_cls.objects.filter(project_id=project.pk)
        else:
            queryset = (model_cls.objects
                            .extra(where=[where_clause], params=[text])
                            .filter(project_id=project.pk)[:50])

        serializer = IssueSerializer(queryset, many=True)
        return serializer.data

    def _search_wiki_pages(self, project, text, get_all):
        where_clause = ("to_tsvector(wiki_wikipage.slug || wiki_wikipage.content) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("wiki", "WikiPage")
        if get_all != "false" and text == '':
            queryset = model_cls.objects.filter(project_id=project.pk)
        else:
            queryset = (model_cls.objects
                            .extra(where=[where_clause], params=[text])
                            .filter(project_id=project.pk)[:50])

        serializer = WikiPageSerializer(queryset, many=True)
        return serializer.data


