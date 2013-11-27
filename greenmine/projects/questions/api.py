# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment

from . import serializers
from . import models
from . import permissions

import reversion


class QuestionAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Question)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        super().pre_save(obj)
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Question)
            obj.owner = self.request.user


class QuestionViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Question
    serializer_class = serializers.QuestionSerializer
    permission_classes = (IsAuthenticated, permissions.QuestionPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)
    create_notification_template = "create_question_notification"
    update_notification_template = "update_question_notification"
    destroy_notification_template = "destroy_question_notification"

    def pre_save(self, obj):
        super().pre_save(obj)
        if not obj.id:
            obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super().post_save(obj, created)
