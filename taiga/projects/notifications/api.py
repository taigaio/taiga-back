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

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet

from taiga.projects.models import Project

from taiga.projects.notifications.choices import NotifyLevel

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
            services.create_notify_policy_if_not_exists(project, self.request.user, NotifyLevel.watch)

    def get_queryset(self):
        self._build_needed_notify_policies()

        qs = models.NotifyPolicy.objects.filter(project__owner=self.request.user)
        return qs.distinct()
