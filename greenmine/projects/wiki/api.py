# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from greenmine.base import filters
from greenmine.base import exceptions as exc
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment

from . import models
from . import permissions
from . import serializers


class WikiAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.WikiPage)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new wiki page to this "
                                        "project.")

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.WikiPage)
            obj.owner = self.request.user

        super().pre_save(obj)


class WikiViewSet(ModelCrudViewSet):
    model = models.WikiPage
    serializer_class = serializers.WikiPageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "slug"]

    def get_historical_queryset(self):
        return super().get_historical_queryset()[1:]

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new wiki page to this "
                                        "project.")

    def pre_save(self, obj):
        if not obj.owner:
            obj.owner = self.request.user

        super().pre_save(obj)
