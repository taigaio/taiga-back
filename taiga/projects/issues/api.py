# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from django.utils.translation import gettext as _
from django.http import HttpResponse

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.decorators import detail_route, list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_error

from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.by_ref import ByRefMixin
from taiga.projects.mixins.promote import PromoteToUserStoryMixin
from taiga.projects.models import Project, IssueStatus, Severity, Priority, IssueType
from taiga.projects.notifications.mixins import AssignedToSignalMixin
from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.notifications.mixins import WatchersViewSetMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.tagging.api import TaggedResourceMixin
from taiga.projects.votes.mixins.viewsets import VotedResourceMixin, VotersViewSetMixin

from .utils import attach_extra_info

from . import models
from . import services
from . import permissions
from . import serializers
from . import validators


class IssueViewSet(AssignedToSignalMixin, OCCResourceMixin, VotedResourceMixin,
                   HistoryResourceMixin, WatchedResourceMixin, ByRefMixin,
                   TaggedResourceMixin, BlockedByProjectMixin, PromoteToUserStoryMixin,
                   ModelCrudViewSet):
    validator_class = validators.IssueValidator
    queryset = models.Issue.objects.all()
    permission_classes = (permissions.IssuePermission, )
    filter_backends = (filters.CanViewIssuesFilterBackend,
                       filters.RoleFilter,
                       filters.OwnersFilter,
                       filters.AssignedToFilter,
                       filters.StatusesFilter,
                       filters.IssueTypesFilter,
                       filters.SeveritiesFilter,
                       filters.PrioritiesFilter,
                       filters.TagsFilter,
                       filters.WatchersFilter,
                       filters.QFilter,
                       filters.CreatedDateFilter,
                       filters.ModifiedDateFilter,
                       filters.FinishedDateFilter,
                       filters.OrderByFilterMixin)
    filter_fields = ("milestone",
                     "project",
                     "project__slug",
                     "status__is_closed")
    order_by_fields = ("type",
                       "project",
                       "status",
                       "severity",
                       "priority",
                       "created_date",
                       "modified_date",
                       "owner",
                       "assigned_to",
                       "subject",
                       "total_voters",
                       "ref")

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
        qs = qs.select_related("owner", "assigned_to", "status", "project")

        include_attachments = "include_attachments" in self.request.QUERY_PARAMS
        qs = attach_extra_info(qs, user=self.request.user,
                               include_attachments=include_attachments)

        return qs

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
    def filters_data(self, request, *args, **kwargs):
        project_id = request.QUERY_PARAMS.get("project", None)
        project = get_object_or_error(Project, request.user, id=project_id)

        filter_backends = self.get_filter_backends()
        types_filter_backends = (f for f in filter_backends if f != filters.IssueTypesFilter)
        statuses_filter_backends = (f for f in filter_backends if f != filters.StatusesFilter)
        assigned_to_filter_backends = (f for f in filter_backends if f != filters.AssignedToFilter)
        owners_filter_backends = (f for f in filter_backends if f != filters.OwnersFilter)
        priorities_filter_backends = (f for f in filter_backends if f != filters.PrioritiesFilter)
        severities_filter_backends = (f for f in filter_backends if f != filters.SeveritiesFilter)
        roles_filter_backends = (f for f in filter_backends if f != filters.RoleFilter)
        tags_filter_backends = (f for f in filter_backends if f != filters.TagsFilter)

        queryset = self.get_queryset()
        querysets = {
            "types": self.filter_queryset(queryset, filter_backends=types_filter_backends),
            "statuses": self.filter_queryset(queryset, filter_backends=statuses_filter_backends),
            "assigned_to": self.filter_queryset(queryset, filter_backends=assigned_to_filter_backends),
            "owners": self.filter_queryset(queryset, filter_backends=owners_filter_backends),
            "priorities": self.filter_queryset(queryset, filter_backends=priorities_filter_backends),
            "severities": self.filter_queryset(queryset, filter_backends=severities_filter_backends),
            "tags": self.filter_queryset(queryset, filter_backends=tags_filter_backends),
            "roles": self.filter_queryset(queryset, filter_backends=roles_filter_backends),
        }
        return response.Ok(services.get_issues_filters_data(project, querysets))

    @list_route(methods=["GET"])
    def csv(self, request):
        uuid = request.QUERY_PARAMS.get("uuid", None)
        if uuid is None:
            return response.NotFound()

        project = get_object_or_error(Project, request.user, issues_csv_uuid=uuid)
        queryset = project.issues.all().order_by('ref')
        data = services.issues_to_csv(project, queryset)
        csv_response = HttpResponse(data.getvalue(), content_type='application/csv; charset=utf-8')
        csv_response['Content-Disposition'] = 'attachment; filename="issues.csv"'
        return csv_response

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        validator = validators.IssuesBulkValidator(data=request.DATA)
        if validator.is_valid():
            data = validator.data
            project = Project.objects.get(pk=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            if project.blocked_code is not None:
                raise exc.Blocked(_("Blocked element"))

            issues = services.create_issues_in_bulk(
                data["bulk_issues"], milestone_id=data["milestone_id"],
                project=project, owner=request.user,
                status=project.default_issue_status,
                severity=project.default_severity,
                priority=project.default_priority,
                type=project.default_issue_type,
                callback=self.post_save, precall=self.pre_save)

            issues = self.get_queryset().filter(id__in=[i.id for i in issues])
            issues_serialized = self.get_serializer_class()(issues, many=True)

            return response.Ok(data=issues_serialized.data)

        return response.BadRequest(validator.errors)

    @list_route(methods=["POST"])
    def bulk_update_milestone(self, request, **kwargs):
        validator = validators.UpdateMilestoneBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_error(Project, request.user, pk=data["project_id"])
        milestone = get_object_or_error(Milestone, request.user, pk=data["milestone_id"])

        self.check_permissions(request, "bulk_update_milestone", project)

        ret = services.update_issues_milestone_in_bulk(data["bulk_issues"], milestone)

        return response.Ok(ret)
    
    @list_route(methods=["POST"])
    def get_ai_suggestion(self, request, **kwargs):
        """Get AI suggestion for an issue description."""
        validator = validators.IssueAISuggestionValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        issue = get_object_or_error(models.Issue, request.user, pk=data["issue_id"])
        self.check_permissions(request, "get_ai_suggestion", issue)

        # TODO: Implement AI suggestion logic here
        suggestion = "This is a placeholder for AI-generated suggestion."

        return response.Ok(suggestion)


class IssueVotersViewSet(VotersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.IssueVotersPermission,)
    resource_model = models.Issue


class IssueWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.IssueWatchersPermission,)
    resource_model = models.Issue
