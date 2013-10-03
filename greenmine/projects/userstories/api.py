# -*- coding: utf-8 -*-

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet
from greenmine.base.notifications.api import NotificationSenderMixin

from . import serializers
from . import models
from . import permissions


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
