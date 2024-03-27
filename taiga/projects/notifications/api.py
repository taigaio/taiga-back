# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.utils import timezone

from taiga.base import response
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import GenericViewSet
from taiga.base.api.utils import get_object_or_error

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
        if self.request.user.is_anonymous:
            return models.NotifyPolicy.objects.none()

        self._build_needed_notify_policies()

        return models.NotifyPolicy.objects.filter(user=self.request.user).filter(
            Q(project__owner=self.request.user) | Q(project__memberships__user=self.request.user)
        ).distinct()


class WebNotificationsViewSet(GenericViewSet):
    serializer_class = serializers.WebNotificationSerializer
    resource_model = models.WebNotification

    def check_permissions(self, request, obj=None):
        return obj and request.user.is_authenticated and \
               request.user.pk == obj.user_id

    def list(self, request):
        if self.request.user.is_anonymous:
            return response.Ok({})

        queryset = models.WebNotification.objects\
            .filter(user=self.request.user)

        if request.GET.get("only_unread", False):
            queryset = queryset.filter(read__isnull=True)

        queryset = queryset.order_by('-read', '-created')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
            return response.Ok({
                "objects": serializer.data,
                "total": queryset.count()
            })

        serializer = self.get_serializer(queryset, many=True)
        return response.Ok(serializer.data)

    def patch(self, request, *args, **kwargs):
        self.check_permissions(request)

        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_error(self.resource_model, request.user, pk=resource_id)
        resource.read = timezone.now()
        resource.save()

        return response.Ok({})

    def post(self, request):
        self.check_permissions(request)

        models.WebNotification.objects.filter(user=self.request.user)\
            .update(read=timezone.now())

        return response.Ok()
