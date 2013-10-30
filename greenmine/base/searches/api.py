# -*- coding: utf-8 -*-

from django.db.models.loading import get_model

from rest_framework.response import Response
from rest_framework import viewsets

from greenmine.base import exceptions as excp
from greenmine.projects.userstories.serializers import UserStorySerializer
from greenmine.projects.tasks.serializers import TaskSerializer
from greenmine.projects.issues.serializers import IssueSerializer
from greenmine.projects.wiki.serializers import WikiPageSerializer


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
        where_clause = ("to_tsvector(userstories_userstory.subject || "
                        "userstories_userstory.description) @@ plainto_tsquery(%s)")

        model_cls = get_model("userstories", "UserStory")
        queryset = (model_cls.objects
                        .extra(where=[where_clause], params=[text])
                        .filter(project_id=project.pk)[:50])

        serializer = UserStorySerializer(queryset, many=True)
        return serializer.data

    def _search_tasks(self, project, text):
        where_clause = ("to_tsvector(tasks_task.subject || tasks_task.description) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("tasks", "Task")
        queryset = (model_cls.objects
                        .extra(where=[where_clause], params=[text])
                        .filter(project_id=project.pk)[:50])

        serializer = TaskSerializer(queryset, many=True)
        return serializer.data

    def _search_issues(self, project, text):
        where_clause = ("to_tsvector(issues_issue.subject || issues_issue.description) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("issues", "Issue")
        queryset = (model_cls.objects
                        .extra(where=[where_clause], params=[text])
                        .filter(project_id=project.pk)[:50])

        serializer = IssueSerializer(queryset, many=True)
        return serializer.data

    def _search_wiki_pages(self, project, text):
        where_clause = ("to_tsvector(wiki_wikipage.slug || wiki_wikipage.content) "
                        "@@ plainto_tsquery(%s)")

        model_cls = get_model("wiki", "WikiPage")
        queryset = (model_cls.objects
                        .extra(where=[where_clause], params=[text])
                        .filter(project_id=project.pk)[:50])

        serializer = WikiPageSerializer(queryset, many=True)
        return serializer.data


