# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment

from . import serializers
from . import models
from . import permissions

import reversion


class PointsViewSet(ModelListViewSet):
    model = models.Points
    serializer_class = serializers.PointsSerializer
    permission_classes = (IsAuthenticated, permissions.PointsPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)


class UserStoryStatusViewSet(ModelListViewSet):
    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)


class UserStoryAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.UserStory)
        qs = super(UserStoryAttachmentViewSet, self).get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        super(UserStoryAttachmentViewSet, self).pre_save(obj)
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.UserStory)
            obj.owner = self.request.user


class UserStoryViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.UserStory
    serializer_class = serializers.UserStorySerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ['project', 'milestone', 'milestone__isnull']
    create_notification_template = "create_userstory_notification"
    update_notification_template = "update_userstory_notification"
    destroy_notification_template = "destroy_userstory_notification"

    def pre_save(self, obj):
        super(UserStoryViewSet, self).pre_save(obj)
        if not obj.id:
            obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
        super(UserStoryViewSet, self).post_save(obj, created)
