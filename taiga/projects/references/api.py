# -*- coding: utf-8 -*-

from django.db.models.loading import get_model
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from taiga.base import exceptions as exc
from .serializers import ResolverSerializer


class ResolverViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        serializer = ResolverSerializer(data=request.QUERY_PARAMS)
        if not serializer.is_valid():
            raise exc.BadRequest(serializer.errors)

        data = serializer.data

        project_model = get_model("projects", "Project")
        project = get_object_or_404(project_model, slug=data["project"])

        result = {
            "project": project.pk
        }

        if data["us"]:
            result["us"] = get_object_or_404(project.user_stories.all(), ref=data["us"]).pk
        if data["task"]:
            result["us"] = get_object_or_404(project.tasks.all(), ref=data["task"]).pk
        if data["issue"]:
            result["issue"] = get_object_or_404(project.issues.all(), ref=data["issue"]).pk
        if data["milestone"]:
            result["milestone"] = get_object_or_404(project.milestones.all(), slug=data["milestone"]).pk

        return Response(result)
