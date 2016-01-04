# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

import uuid

from django.db.models import signals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from taiga.base import filters
from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.permissions import AllowAnyPermission
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils.slug import slugify_uniquely

from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.notifications.utils import (
    attach_project_total_watchers_attrs_to_queryset,
    attach_project_is_watcher_to_queryset,
    attach_notify_level_to_project_queryset)

from taiga.projects.mixins.ordering import BulkUpdateOrderMixin
from taiga.projects.mixins.on_destroy import MoveOnDestroyMixin

from taiga.projects.userstories.models import UserStory, RolePoints
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.likes.mixins.viewsets import LikedResourceMixin, FansViewSetMixin
from taiga.permissions import service as permissions_service

from . import serializers
from . import models
from . import permissions
from . import services


######################################################
## Project
######################################################
class ProjectViewSet(LikedResourceMixin, HistoryResourceMixin, ModelCrudViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectDetailSerializer
    admin_serializer_class = serializers.ProjectDetailAdminSerializer
    list_serializer_class = serializers.ProjectSerializer
    permission_classes = (permissions.ProjectPermission, )
    filter_backends = (filters.CanViewProjectObjFilterBackend,)
    filter_fields = (('member', 'members'),)
    order_by_fields = ("memberships__user_order",)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.attach_likes_attrs_to_queryset(qs)
        qs = attach_project_total_watchers_attrs_to_queryset(qs)
        if self.request.user.is_authenticated():
            qs = attach_project_is_watcher_to_queryset(qs, self.request.user)
            qs = attach_notify_level_to_project_queryset(qs, self.request.user)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return self.list_serializer_class
        elif self.action == "create":
            return self.serializer_class

        if self.action == "by_slug":
            slug = self.request.QUERY_PARAMS.get("slug", None)
            project = get_object_or_404(models.Project, slug=slug)
        else:
            project = self.get_object()

        if permissions_service.is_project_owner(self.request.user, project):
            return self.admin_serializer_class

        return self.serializer_class

    @detail_route(methods=["POST"])
    def watch(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "watch", project)
        notify_level = request.DATA.get("notify_level", NotifyLevel.involved)
        project.add_watcher(self.request.user, notify_level=notify_level)
        return response.Ok()

    @detail_route(methods=["POST"])
    def unwatch(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "unwatch", project)
        user = self.request.user
        project.remove_watcher(user)
        return response.Ok()

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        if self.request.user.is_anonymous():
            return response.Unauthorized()

        serializer = serializers.UpdateProjectOrderBulkSerializer(data=request.DATA, many=True)
        if not serializer.is_valid():
            return response.BadRequest(serializer.errors)

        data = serializer.data
        services.update_projects_order_in_bulk(data, "user_order", request.user)
        return response.NoContent(data=None)

    @list_route(methods=["GET"])
    def by_slug(self, request):
        slug = request.QUERY_PARAMS.get("slug", None)
        project = get_object_or_404(models.Project, slug=slug)
        return self.retrieve(request, pk=project.pk)

    @detail_route(methods=["GET", "PATCH"])
    def modules(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'modules', project)
        modules_config = services.get_modules_config(project)

        if request.method == "GET":
            return response.Ok(modules_config.config)

        else:
            modules_config.config.update(request.DATA)
            modules_config.save()
            return response.NoContent()

    @detail_route(methods=["GET"])
    def stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "stats", project)
        return response.Ok(services.get_stats_for_project(project))

    def _regenerate_csv_uuid(self, project, field):
        uuid_value = uuid.uuid4().hex
        setattr(project, field, uuid_value)
        project.save()
        return uuid_value

    @detail_route(methods=["POST"])
    def regenerate_userstories_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_userstories_csv_uuid", project)
        data = {"uuid": self._regenerate_csv_uuid(project, "userstories_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def regenerate_issues_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_issues_csv_uuid", project)
        data = {"uuid": self._regenerate_csv_uuid(project, "issues_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def regenerate_tasks_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_tasks_csv_uuid", project)
        data = {"uuid": self._regenerate_csv_uuid(project, "tasks_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["GET"])
    def member_stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "member_stats", project)
        return response.Ok(services.get_member_stats_for_project(project))

    @detail_route(methods=["GET"])
    def issues_stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "issues_stats", project)
        return response.Ok(services.get_stats_for_project_issues(project))

    @detail_route(methods=["GET"])
    def tags_colors(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "tags_colors", project)
        return response.Ok(dict(project.tags_colors))

    @detail_route(methods=["POST"])
    def create_template(self, request, **kwargs):
        template_name = request.DATA.get('template_name', None)
        template_description = request.DATA.get('template_description', None)

        if not template_name:
            raise response.BadRequest(_("Not valid template name"))

        if not template_description:
            raise response.BadRequest(_("Not valid template description"))

        template_slug = slugify_uniquely(template_name, models.ProjectTemplate)

        project = self.get_object()

        self.check_permissions(request, 'create_template', project)

        template = models.ProjectTemplate(
            name=template_name,
            slug=template_slug,
            description=template_description,
        )

        template.load_data_from_project(project)
        template.save()
        return response.Created(serializers.ProjectTemplateSerializer(template).data)

    @detail_route(methods=['post'])
    def leave(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'leave', project)
        services.remove_user_from_project(request.user, project)
        return response.Ok()

    def _set_base_permissions(self, obj):
        update_permissions = False
        if not obj.id:
            if not obj.is_private:
                # Creating a public project
                update_permissions = True
        else:
            if self.get_object().is_private != obj.is_private:
                # Changing project public state
                update_permissions = True

        if update_permissions:
            permissions_service.set_base_permissions_for_project(obj)

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        # TODO REFACTOR THIS
        if not obj.id:
            obj.template = self.request.QUERY_PARAMS.get('template', None)

        self._set_base_permissions(obj)
        super().pre_save(obj)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object_or_none()
        self.check_permissions(request, 'destroy', obj)

        if obj is None:
            raise Http404

        obj.delete_related_content()

        self.pre_delete(obj)
        self.pre_conditions_on_delete(obj)
        obj.delete()
        self.post_delete(obj)
        return response.NoContent()


class ProjectFansViewSet(FansViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.ProjectFansPermission,)
    resource_model = models.Project


class ProjectWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.ProjectWatchersPermission,)
    resource_model = models.Project

######################################################
## Custom values for selectors
######################################################

class PointsViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Points
    serializer_class = serializers.PointsSerializer
    permission_classes = (permissions.PointsPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_points"
    bulk_update_perm = "change_points"
    bulk_update_order_action = services.bulk_update_points_order
    move_on_destroy_related_class = RolePoints
    move_on_destroy_related_field = "points"
    move_on_destroy_project_default_field = "default_points"

class UserStoryStatusViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    permission_classes = (permissions.UserStoryStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_userstory_statuses"
    bulk_update_perm = "change_userstorystatus"
    bulk_update_order_action = services.bulk_update_userstory_status_order
    move_on_destroy_related_class = UserStory
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_us_status"


class TaskStatusViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    permission_classes = (permissions.TaskStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_task_statuses"
    bulk_update_perm = "change_taskstatus"
    bulk_update_order_action = services.bulk_update_task_status_order
    move_on_destroy_related_class = Task
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_task_status"


class SeverityViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Severity
    serializer_class = serializers.SeveritySerializer
    permission_classes = (permissions.SeverityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_severities"
    bulk_update_perm = "change_severity"
    bulk_update_order_action = services.bulk_update_severity_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "severity"
    move_on_destroy_project_default_field = "default_severity"


class PriorityViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Priority
    serializer_class = serializers.PrioritySerializer
    permission_classes = (permissions.PriorityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_priorities"
    bulk_update_perm = "change_priority"
    bulk_update_order_action = services.bulk_update_priority_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "priority"
    move_on_destroy_project_default_field = "default_priority"


class IssueTypeViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueType
    serializer_class = serializers.IssueTypeSerializer
    permission_classes = (permissions.IssueTypePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_types"
    bulk_update_perm = "change_issuetype"
    bulk_update_order_action = services.bulk_update_issue_type_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "type"
    move_on_destroy_project_default_field = "default_issue_type"


class IssueStatusViewSet(MoveOnDestroyMixin, ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueStatus
    serializer_class = serializers.IssueStatusSerializer
    permission_classes = (permissions.IssueStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_statuses"
    bulk_update_perm = "change_issuestatus"
    bulk_update_order_action = services.bulk_update_issue_status_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_issue_status"


######################################################
## Project Template
######################################################

class ProjectTemplateViewSet(ModelCrudViewSet):
    model = models.ProjectTemplate
    serializer_class = serializers.ProjectTemplateSerializer
    permission_classes = (permissions.ProjectTemplatePermission,)

    def get_queryset(self):
        return models.ProjectTemplate.objects.all()


######################################################
## Members & Invitations
######################################################

class MembershipViewSet(ModelCrudViewSet):
    model = models.Membership
    admin_serializer_class = serializers.MembershipAdminSerializer
    serializer_class = serializers.MembershipSerializer
    permission_classes = (permissions.MembershipPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project", "role")

    def get_serializer_class(self):
        project_id = self.request.QUERY_PARAMS.get("project", None)
        if project_id is None:
            # Creation
            if self.request.method == 'POST':
                return self.admin_serializer_class

            return self.serializer_class

        project = get_object_or_404(models.Project, pk=project_id)
        if permissions_service.is_project_owner(self.request.user, project):
            return self.admin_serializer_class

        return self.serializer_class

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        serializer = serializers.MembersBulkSerializer(data=request.DATA)
        if not serializer.is_valid():
            return response.BadRequest(serializer.errors)

        data = serializer.data
        project = models.Project.objects.get(id=data["project_id"])
        invitation_extra_text = data.get("invitation_extra_text", None)
        self.check_permissions(request, 'bulk_create', project)

        # TODO: this should be moved to main exception handler instead
        # of handling explicit exception catchin here.

        try:
            members = services.create_members_in_bulk(data["bulk_memberships"],
                                                      project=project,
                                                      invitation_extra_text=invitation_extra_text,
                                                      callback=self.post_save,
                                                      precall=self.pre_save)
        except ValidationError as err:
            return response.BadRequest(err.message_dict)

        members_serialized = self.admin_serializer_class(members, many=True)
        return response.Ok(members_serialized.data)

    @detail_route(methods=["POST"])
    def resend_invitation(self, request, **kwargs):
        invitation = self.get_object()

        self.check_permissions(request, 'resend_invitation', invitation.project)

        services.send_invitation(invitation=invitation)
        return response.NoContent()

    def pre_delete(self, obj):
        if obj.user is not None and not services.can_user_leave_project(obj.user, obj.project):
            raise exc.BadRequest(_("At least one of the user must be an active admin"))

    def pre_save(self, obj):
        if not obj.token:
            obj.token = str(uuid.uuid1())

        obj.invited_by = self.request.user
        obj.user = services.find_invited_user(obj.email, default=obj.user)
        super().pre_save(obj)

    def post_save(self, object, created=False):
        super().post_save(object, created=created)

        if not created:
            return

        # Send email only if a new membership is created
        services.send_invitation(invitation=object)


class InvitationViewSet(ModelListViewSet):
    """
    Only used by front for get invitation by it token.
    """
    queryset = models.Membership.objects.filter(user__isnull=True)
    serializer_class = serializers.MembershipSerializer
    lookup_field = "token"
    permission_classes = (AllowAnyPermission,)

    def list(self, *args, **kwargs):
        raise exc.PermissionDenied(_("You don't have permisions to see that."))
