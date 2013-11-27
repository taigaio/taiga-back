# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base import exceptions as exc
from greenmine.base.api import ModelCrudViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment

from . import models
from . import permissions
from . import serializers

import reversion


class TaskAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Task)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Task)
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new task attachment "
                                        "to this project.")



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
        if obj.user_story:
            obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new task to this project.")

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PreconditionError("You must not add a task to this milestone.")

        if obj.user_story and obj.user_story.project != obj.project:
            raise exc.PreconditionError("You must not add a task to this user story.")

        if obj.status and obj.status.project != obj.project:
            raise exc.PreconditionError("You must not use a status from other project.")

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super().post_save(obj, created)
