# -*- coding: utf-8 -*-
from django.db.models import Q

from taiga.base import response
from taiga.base.api import ModelCrudViewSet, ReadOnlyListViewSet

from taiga.projects.settings.choices import HOMEPAGE_CHOICES
from taiga.projects.models import Project

from . import models
from . import permissions
from . import serializers
from . import services
from . import validators


class UserProjectSettingsViewSet(ModelCrudViewSet):
    serializer_class = serializers.UserProjectSettingsSerializer
    permission_classes = (permissions.UserProjectSettingsPermission,)
    validator_class = validators.UserProjectSettingsValidator

    def _build_user_project_settings(self):
        projects = Project.objects.filter(
            Q(owner=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct()

        for project in projects:
            services.create_user_project_settings_if_not_exists(
                project, self.request.user)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.UserProjectSettings.objects.none()

        self._build_user_project_settings()

        return models.UserProjectSettings.objects.filter(user=self.request.user)\
            .filter(project__memberships__user=self.request.user)\
            .order_by('project__memberships__user_order')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        project_id = request.QUERY_PARAMS.get("project", None)
        if project_id:
            qs = qs.filter(project_id=project_id)

        serializer = self.get_serializer(qs, many=True)

        return response.Ok(serializer.data)


class SectionsViewSet(ReadOnlyListViewSet):
    def list(self, request, *args, **kwargs):
        return response.Response(HOMEPAGE_CHOICES)
