# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import reversion
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet, NeighborsApiMixin
from taiga.base.notifications.api import NotificationSenderMixin
from taiga.projects.permissions import AttachmentPermission
from taiga.projects.serializers import AttachmentSerializer
from taiga.projects.models import Attachment

from . import models
from . import permissions
from . import serializers


class IssuesFilter(filters.FilterBackend):
    filter_fields = ( "status", "severity", "priority", "owner", "assigned_to", "tags", "type")
    _special_values_dict = {
        'true': True,
        'false': False,
        'null': None,
    }

    def _prepare_filters_data(self, request):
        def _transform_value(value):
            try:
                return int(value)
            except:
                if value in self._special_values_dict.keys():
                    return self._special_values_dict[value]
            raise exc.BadRequest()

        data = {}
        for filtername in self.filter_fields:
            if filtername not in request.QUERY_PARAMS:
                continue

            raw_value = request.QUERY_PARAMS[filtername]
            values = set([x.strip() for x in raw_value.split(",")])

            if filtername != "tags":
                values = map(_transform_value, values)

            data[filtername] = list(values)
        return data

    def filter_queryset(self, request, queryset, view):
        filterdata = self._prepare_filters_data(request)

        if "tags" in filterdata:
            where_sql = ["unpickle(issues_issue.tags) @> %s"]
            params = [filterdata["tags"]]
            queryset = queryset.extra(where=where_sql, params=params)

        for name, value in filter(lambda x: x[0] != "tags", filterdata.items()):
            if None in value:
                qs_in_kwargs = {"{0}__in".format(name): [v for v in value if v != None]}
                qs_isnull_kwargs = {"{0}__isnull".format(name): True}
                queryset = queryset.filter(Q(**qs_in_kwargs) | Q(**qs_isnull_kwargs))
            else:
                qs_kwargs = {"{0}__in".format(name): value}
                queryset = queryset.filter(**qs_kwargs)

        return queryset

class IssuesOrdering(filters.FilterBackend):
    def filter_queryset(self, request, queryset, view):
        order_by = request.QUERY_PARAMS.get('order_by', None)
        if order_by in ['owner', '-owner', 'assigned_to', '-assigned_to']:
            return queryset.order_by(
                '{}__first_name'.format(order_by),
                '{}__last_name'.format(order_by)
            )
        return queryset


class IssueViewSet(NeighborsApiMixin, NotificationSenderMixin, ModelCrudViewSet):
    model = models.Issue
    queryset = models.Issue.objects.all().prefetch_related("attachments")
    serializer_class = serializers.IssueNeighborsSerializer
    list_serializer_class = serializers.IssueSerializer
    permission_classes = (IsAuthenticated, permissions.IssuePermission)

    filter_backends = (filters.IsProjectMemberFilterBackend, IssuesFilter, IssuesOrdering)
    retrieve_exclude_filters = (IssuesFilter,)
    filter_fields = ("project",)
    order_by_fields = ("severity", "status", "priority", "created_date", "modified_date", "owner",
                       "assigned_to", "subject")

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
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

        if obj.status and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

        if obj.severity and obj.severity.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

        if obj.priority and obj.priority.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

        if obj.type and obj.type.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this issue."))

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
            raise exc.PermissionDenied(_("You don't have permissions for add attachments "
                                         "to this issue"))
