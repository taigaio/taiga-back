# -*- coding: utf-8 -*-

from django.db.models import Q

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet
from greenmine.base.notifications.api import NotificationSenderMixin

from . import serializers
from . import models
from . import permissions


class ProjectViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Project
    serializer_class = serializers.ProjectSerializer
    permission_classes = (IsAuthenticated, permissions.ProjectPermission)
    create_notification_template = "create_project_notification"
    update_notification_template = "update_project_notification"
    destroy_notification_template = "destroy_project_notification"

    def get_queryset(self):
        qs = super(ProjectViewSet, self).get_queryset()
        qs = qs.filter(Q(owner=self.request.user) |
                       Q(members=self.request.user))
        return qs.distinct()

    def pre_save(self, obj):
        super(ProjectViewSet, self).pre_save(obj)
        obj.owner = self.request.user
