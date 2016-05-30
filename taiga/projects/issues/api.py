# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from django.http import HttpResponse

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_404

from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.history.mixins import HistoryResourceMixin

from taiga.projects.models import Project, IssueStatus, Severity, Priority, IssueType
from taiga.projects.votes.mixins.viewsets import VotedResourceMixin, VotersViewSetMixin

from . import models
from . import services
from . import permissions
from . import serializers


class IssueViewSet(OCCResourceMixin, VotedResourceMixin, HistoryResourceMixin, WatchedResourceMixin,
                   BlockedByProjectMixin, ModelCrudViewSet):
    queryset = models.Issue.objects.all()
    permission_classes = (permissions.IssuePermission, )
    filter_backends = (filters.CanViewIssuesFilterBackend,
                       filters.OwnersFilter,
                       filters.AssignedToFilter,
                       filters.StatusesFilter,
                       filters.IssueTypesFilter,
                       filters.SeveritiesFilter,
                       filters.PrioritiesFilter,
                       filters.TagsFilter,
                       filters.WatchersFilter,
                       filters.QFilter,
                       filters.OrderByFilterMixin)
    retrieve_exclude_filters = (filters.OwnersFilter,
                                filters.AssignedToFilter,
                                filters.StatusesFilter,
                                filters.IssueTypesFilter,
                                filters.SeveritiesFilter,
                                filters.PrioritiesFilter,
                                filters.TagsFilter,
                                filters.WatchersFilter,)

    filter_fields = ("project",
                     "status__is_closed")

    order_by_fields = ("type",
                       "status",
                       "severity",
                       "priority",
                       "created_date",
                       "modified_date",
                       "owner",
                       "assigned_to",
                       "subject",
                       "total_voters")

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.IssueNeighborsSerializer

        if self.action == "list":
            return serializers.IssueListSerializer

        return serializers.IssueSerializer

    def update(self, request, *args, **kwargs):
        self.object = self.get_object_or_none()
        project_id = request.DATA.get('project', None)
        if project_id and self.object and self.object.project.id != project_id:
            try:
                new_project = Project.objects.get(pk=project_id)
                self.check_permissions(request, "destroy", self.object)
                self.check_permissions(request, "create", new_project)

                sprint_id = request.DATA.get('milestone', None)
                if sprint_id is not None and new_project.milestones.filter(pk=sprint_id).count() == 0:
                    request.DATA['milestone'] = None

                status_id = request.DATA.get('status', None)
                if status_id is not None:
                    try:
                        old_status = self.object.project.issue_statuses.get(pk=status_id)
                        new_status = new_project.issue_statuses.get(slug=old_status.slug)
                        request.DATA['status'] = new_status.id
                    except IssueStatus.DoesNotExist:
                        request.DATA['status'] = new_project.default_issue_status.id

                priority_id = request.DATA.get('priority', None)
                if priority_id is not None:
                    try:
                        old_priority = self.object.project.priorities.get(pk=priority_id)
                        new_priority = new_project.priorities.get(name=old_priority.name)
                        request.DATA['priority'] = new_priority.id
                    except Priority.DoesNotExist:
                        request.DATA['priority'] = new_project.default_priority.id

                severity_id = request.DATA.get('severity', None)
                if severity_id is not None:
                    try:
                        old_severity = self.object.project.severities.get(pk=severity_id)
                        new_severity = new_project.severities.get(name=old_severity.name)
                        request.DATA['severity'] = new_severity.id
                    except Severity.DoesNotExist:
                        request.DATA['severity'] = new_project.default_severity.id

                type_id = request.DATA.get('type', None)
                if type_id is not None:
                    try:
                        old_type = self.object.project.issue_types.get(pk=type_id)
                        new_type = new_project.issue_types.get(name=old_type.name)
                        request.DATA['type'] = new_type.id
                    except IssueType.DoesNotExist:
                        request.DATA['type'] = new_project.default_issue_type.id

            except Project.DoesNotExist:
                return response.BadRequest(_("The project doesn't exist"))

        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related("attachments", "generated_user_stories")
        qs = qs.select_related("owner", "assigned_to", "status", "project")
        qs = self.attach_votes_attrs_to_queryset(qs)
        return self.attach_watchers_attrs_to_queryset(qs)

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
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

        super().pre_conditions_on_save(obj)

    @list_route(methods=["GET"])
    def by_ref(self, request):
        ref = request.QUERY_PARAMS.get("ref", None)
        project_id = request.QUERY_PARAMS.get("project", None)
        issue = get_object_or_404(models.Issue, ref=ref, project_id=project_id)
        return self.retrieve(request, pk=issue.pk)

    @list_route(methods=["GET"])
    def filters_data(self, request, *args, **kwargs):
        project_id = request.QUERY_PARAMS.get("project", None)
        project = get_object_or_404(Project, id=project_id)

        filter_backends = self.get_filter_backends()
        types_filter_backends = (f for f in filter_backends if f != filters.IssueTypesFilter)
        statuses_filter_backends = (f for f in filter_backends if f != filters.StatusesFilter)
        assigned_to_filter_backends = (f for f in filter_backends if f != filters.AssignedToFilter)
        owners_filter_backends = (f for f in filter_backends if f != filters.OwnersFilter)
        priorities_filter_backends = (f for f in filter_backends if f != filters.PrioritiesFilter)
        severities_filter_backends = (f for f in filter_backends if f != filters.SeveritiesFilter)
        tags_filter_backends = (f for f in filter_backends if f != filters.TagsFilter)

        queryset = self.get_queryset()
        querysets = {
            "types": self.filter_queryset(queryset, filter_backends=types_filter_backends),
            "statuses": self.filter_queryset(queryset, filter_backends=statuses_filter_backends),
            "assigned_to": self.filter_queryset(queryset, filter_backends=assigned_to_filter_backends),
            "owners": self.filter_queryset(queryset, filter_backends=owners_filter_backends),
            "priorities": self.filter_queryset(queryset, filter_backends=priorities_filter_backends),
            "severities": self.filter_queryset(queryset, filter_backends=severities_filter_backends),
            "tags": self.filter_queryset(queryset)
        }
        return response.Ok(services.get_issues_filters_data(project, querysets))

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
            if project.blocked_code is not None:
                raise exc.Blocked(_("Blocked element"))

            issues = services.create_issues_in_bulk(
                data["bulk_issues"], project=project, owner=request.user,
                status=project.default_issue_status, severity=project.default_severity,
                priority=project.default_priority, type=project.default_issue_type,
                callback=self.post_save, precall=self.pre_save)
            issues_serialized = self.get_serializer_class()(issues, many=True)

            return response.Ok(data=issues_serialized.data)

        return response.BadRequest(serializer.errors)


class IssueVotersViewSet(VotersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.IssueVotersPermission,)
    resource_model = models.Issue


class IssueWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.IssueWatchersPermission,)
    resource_model = models.Issue
