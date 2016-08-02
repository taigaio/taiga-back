# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base.api import ModelCrudViewSet

from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.models import Project
from . import serializers
from . import models
from . import permissions
from . import services


class NotifyPolicyViewSet(ModelCrudViewSet):
    serializer_class = serializers.NotifyPolicySerializer
    permission_classes = (permissions.NotifyPolicyPermission,)

    def _build_needed_notify_policies(self):
        projects = Project.objects.filter(
            Q(owner=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct()

        for project in projects:
            services.create_notify_policy_if_not_exists(project, self.request.user, NotifyLevel.all)

    def get_queryset(self):
        if self.request.user.is_anonymous():
            return models.NotifyPolicy.objects.none()

        self._build_needed_notify_policies()

        return models.NotifyPolicy.objects.filter(user=self.request.user).filter(
            Q(project__owner=self.request.user) | Q(project__memberships__user=self.request.user)
        ).distinct()
