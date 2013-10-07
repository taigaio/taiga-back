# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment

from . import models
from . import permissions
from . import serializers

import reversion


class TaskStatusViewSet(ModelListViewSet):
    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    permission_classes = (IsAuthenticated, permissions.TaskStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


class TaskAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Task)
        qs = super(TaskAttachmentViewSet, self).get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        super(TaskAttachmentViewSet, self).pre_save(obj)
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Task)
            obj.owner = self.request.user


class TaskViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Task
    serializer_class = serializers.TaskSerializer
    permission_classes = (IsAuthenticated, permissions.TaskPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["user_story", "milestone", "project"]
    create_notification_template = "create_task_notification"
    update_notification_template = "update_task_notification"
    destroy_notification_template = "destroy_task_notification"

    def pre_save(self, obj):
        super(TaskViewSet, self).pre_save(obj)
        obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super(TaskViewSet, self).post_save(obj, created)
