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

from django.utils.translation import ugettext as _
from django.db.models import Q
from django.http import Http404, HttpResponse

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.decorators import detail_route, list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.utils import get_object_or_404

from taiga.users.models import User

from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.history.mixins import HistoryResourceMixin

from taiga.projects.models import Project
from taiga.projects.votes.utils import attach_votescount_to_queryset
from taiga.projects.votes import services as votes_service
from taiga.projects.votes import serializers as votes_serializers
from . import models
from . import services
from . import permissions
from . import serializers


class IssuesFilter(filters.FilterBackend):
    filter_fields = ("status", "severity", "priority", "owner", "assigned_to", "tags", "type")
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
            queryset = queryset.filter(tags__contains=filterdata["tags"])

        for name, value in filter(lambda x: x[0] != "tags", filterdata.items()):
            if None in value:
                qs_in_kwargs = {"{0}__in".format(name): [v for v in value if v is not None]}
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
                '{}__full_name'.format(order_by)
            )
        return queryset


class IssueViewSet(OCCResourceMixin, HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    permission_classes = (permissions.IssuePermission, )

    filter_backends = (filters.CanViewIssuesFilterBackend, filters.QFilter,
                       IssuesFilter, IssuesOrdering,)
    retrieve_exclude_filters = (IssuesFilter,)

    filter_fields = ("project", "status__is_closed", "watchers")
    order_by_fields = ("type",
                       "severity",
                       "status",
                       "priority",
                       "created_date",
                       "modified_date",
                       "owner",
                       "assigned_to",
                       "subject")

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.IssueNeighborsSerializer

        if self.action == "list":
            return serializers.IssueListSerializer

        return serializers.IssueSerializer

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

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this sprint "
                                         "to this issue."))

        if obj.status and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this status "
                                         "to this issue."))

        if obj.severity and obj.severity.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this severity "
                                         "to this issue."))

        if obj.priority and obj.priority.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this priority "
                                         "to this issue."))

        if obj.type and obj.type.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this type "
                                         "to this issue."))

    @list_route(methods=["GET"])
    def by_ref(self, request):
        ref = request.QUERY_PARAMS.get("ref", None)
        project_id = request.QUERY_PARAMS.get("project", None)
        issue = get_object_or_404(models.Issue, ref=ref, project_id=project_id)
        return self.retrieve(request, pk=issue.pk)

    @list_route(methods=["GET"])
    def csv(self, request):
        uuid = request.QUERY_PARAMS.get("uuid", None)
        if uuid is None:
            return response.NotFound()

        project = get_object_or_404(Project, issues_csv_uuid=uuid)
        queryset = project.issues.all().order_by('ref')
        data = services.issues_to_csv(project, queryset)
        csv_response = HttpResponse(data.getvalue(), content_type='application/csv; charset=utf-8')
        csv_response['Content-Disposition'] = 'attachment; filename="issues.csv"'
        return csv_response

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        serializer = serializers.IssuesBulkSerializer(data=request.DATA)
        if serializer.is_valid():
            data = serializer.data
            project = Project.objects.get(pk=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            issues = services.create_issues_in_bulk(
                data["bulk_issues"], project=project, owner=request.user,
                status=project.default_issue_status, severity=project.default_severity,
                priority=project.default_priority, type=project.default_issue_type,
                callback=self.post_save, precall=self.pre_save)
            issues_serialized = self.get_serializer_class()(issues, many=True)

            return response.Ok(data=issues_serialized.data)

        return response.BadRequest(serializer.errors)

    @detail_route(methods=['post'])
    def upvote(self, request, pk=None):
        issue = get_object_or_404(models.Issue, pk=pk)

        self.check_permissions(request, 'upvote', issue)

        votes_service.add_vote(issue, user=request.user)
        return response.Ok()

    @detail_route(methods=['post'])
    def downvote(self, request, pk=None):
        issue = get_object_or_404(models.Issue, pk=pk)

        self.check_permissions(request, 'downvote', issue)

        votes_service.remove_vote(issue, user=request.user)
        return response.Ok()


class VotersViewSet(ModelListViewSet):
    serializer_class = votes_serializers.VoterSerializer
    list_serializer_class = votes_serializers.VoterSerializer
    permission_classes = (permissions.IssueVotersPermission, )

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        issue_id = kwargs.get("issue_id", None)
        issue = get_object_or_404(models.Issue, pk=issue_id)

        self.check_permissions(request, 'retrieve', issue)

        try:
            self.object = votes_service.get_voters(issue).get(pk=pk)
        except User.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def list(self, request, *args, **kwargs):
        issue_id = kwargs.get("issue_id", None)
        issue = get_object_or_404(models.Issue, pk=issue_id)
        self.check_permissions(request, 'list', issue)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        issue = models.Issue.objects.get(pk=self.kwargs.get("issue_id"))
        return votes_service.get_voters(issue)
