# -*- coding: utf-8 -*-

from django.db.models.loading import get_model

from rest_framework.response import Response
from rest_framework import viewsets

from haystack import query, inputs

from greenmine.base import exceptions as excp

from .serializers import SearchSerializer


class SearchViewSet(viewsets.ViewSet):
    def list(self, request, **kwargs):
        project_model = get_model("projects", "Project")
        text = request.QUERY_PARAMS.get('text', "")
        project_id = request.QUERY_PARAMS.get('project', None)

        try:
            project = self._get_project(project_id)
        except (project_model.DoesNotExist, TypeError):
            raise excp.PermissionDenied({"detail": "Wrong project id"})

        #if not text:
        #    raise excp.BadRequest("text parameter must be contains text")

        queryset = query.SearchQuerySet()
        queryset = queryset.filter(text=inputs.AutoQuery(text))
        queryset = queryset.filter(project_id=project_id)

        return_data = SearchSerializer(queryset)
        return Response(return_data.data)

    def _get_project(self, project_id):
        project_model = get_model("projects", "Project")
        own_projects = (project_model.objects
                            .filter(members=self.request.user))

        return own_projects.get(pk=project_id)
