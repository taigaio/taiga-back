# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ParseError

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
        if not obj.id:
            obj.owner = self.request.user

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise ParseError(detail=_("You must not add a new milestone to this project."))
