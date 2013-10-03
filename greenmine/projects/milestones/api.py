# -*- coding: utf-8 -*-

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet
from greenmine.base.notifications.api import NotificationSenderMixin

from . import serializers
from . import models
from . import permissions


class MilestoneViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model= models.Milestone
    serializer_class = serializers.MilestoneSerializer
    permission_classes = (IsAuthenticated, permissions.MilestonePermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)
    create_notification_template = "create_milestone_notification"
    update_notification_template = "update_milestone_notification"
    destroy_notification_template = "destroy_milestone_notification"

    def pre_save(self, obj):
        super(MilestoneViewSet, self).pre_save(obj)
        obj.owner = self.request.user


