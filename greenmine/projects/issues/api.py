# -*- coding: utf-8 -*-

import reversion
from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

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

class IssuesFilter(filters.FilterBackend):
    filter_fields = ( "status", "severity", "priority", "owner", "assigned_to", "tags")

    def _prepare_filters_data(self, request):
        data = {}
        for filtername in self.filter_fields:
            if filtername not in request.QUERY_PARAMS:
                continue

            raw_value = request.QUERY_PARAMS[filtername]
            values = (x.strip() for x in raw_value.split(","))

            if filtername != "tags":
                values = map(int, values)

            data[filtername] = list(values)
        return data

    def filter_queryset(self, request, queryset, view):
        filterdata = self._prepare_filters_data(request)

        if "tags" in filterdata:
            where_sql = ["unpickle(issues_issue.tags) @> %s"]
            params = [filterdata["tags"]]
            queryset = queryset.extra(where=where_sql, params=params)

        for name, value in filter(lambda x: x[0] != "tags", filterdata.items()):
            qs_kwargs = {"{0}_id__in".format(name): value}
            queryset = queryset.filter(**qs_kwargs)

        return queryset


class IssueViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Issue
    serializer_class = serializers.IssueSerializer
    permission_classes = (IsAuthenticated, permissions.IssuePermission)

    filter_backends = (filters.IsProjectMemberFilterBackend, IssuesFilter)
    filter_fields = ("project",)
    order_by_fields = ("severity", "status", "priority", "created_date", "modified_date", "owner",
                       "assigned_to")

    create_notification_template = "create_issue_notification"
    update_notification_template = "update_issue_notification"
    destroy_notification_template = "destroy_issue_notification"

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new issue to this project.")

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PreconditionError("You must not add a new issue to this milestone.")

        if obj.status and obj.status.project != obj.project:
            raise exc.PreconditionError("You must not use a status from other project.")

        if obj.severity and obj.severity.project != obj.project:
            raise exc.PreconditionError("You must not use a severity from other project.")

        if obj.priority and obj.priority.project != obj.project:
            raise exc.PreconditionError("You must not use a priority from other project.")

        if obj.type and obj.type.project != obj.project:
            raise exc.PreconditionError("You must not use a type from other project.")

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super().post_save(obj, created)


class IssueAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Issue)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Issue)
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new issue attachment "
                                        "to this project.")
