# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
