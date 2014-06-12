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

from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route, detail_route
from taiga.base.api import ModelCrudViewSet

from taiga.projects.notifications import WatchedResourceMixin
from taiga.projects.history import HistoryResourceMixin


from taiga.projects.votes.utils import attach_votescount_to_queryset
from taiga.projects.votes import services as votes_service
from taiga.projects.votes import serializers as votes_serializers
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


class IssueViewSet(HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    serializer_class = serializers.IssueNeighborsSerializer
    list_serializer_class = serializers.IssueSerializer
    permission_classes = (IsAuthenticated, permissions.IssuePermission)

    filter_backends = (filters.IsProjectMemberFilterBackend, IssuesFilter, IssuesOrdering)
    retrieve_exclude_filters = (IssuesFilter,)

    filter_fields = ("project",)
    order_by_fields = ("severity",
                       "status",
                       "priority",
                       "created_date",
                       "modified_date",
                       "owner",
                       "assigned_to",
                       "subject")

    def get_queryset(self):
        qs = models.Issue.objects.all()
        qs = qs.prefetch_related("attachments")
        qs = attach_votescount_to_queryset(qs, as_field="votes_count")
        return qs

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

    @detail_route(methods=['post'], permission_classes=(IsAuthenticated,))
    def upvote(self, request, pk=None):
        issue = self.get_object()
        votes_service.add_vote(issue, user=request.user)
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['post'], permission_classes=(IsAuthenticated,))
    def downvote(self, request, pk=None):
        issue = self.get_object()
        votes_service.remove_vote(issue, user=request.user)
        return Response(status=status.HTTP_200_OK)


class VotersViewSet(ModelCrudViewSet):
    serializer_class = votes_serializers.VoterSerializer
    list_serializer_class = votes_serializers.VoterSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        issue = models.Issue.objects.get(pk=self.kwargs.get("issue_id"))
        return votes_service.get_voters(issue)
