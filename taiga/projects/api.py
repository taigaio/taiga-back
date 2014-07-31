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

import uuid

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework import viewsets
from rest_framework import status

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import RetrieveModelMixin
from taiga.base.api.permissions import IsAuthenticatedPermission, AllowAnyPermission
from taiga.base.utils.slug import slugify_uniquely
from taiga.users.models import Role

from . import serializers
from . import models
from . import permissions
from . import services

from .votes.utils import attach_votescount_to_queryset
from .votes import services as votes_service
from .votes import serializers as votes_serializers


class ProjectViewSet(ModelCrudViewSet):
    serializer_class = serializers.ProjectDetailSerializer
    list_serializer_class = serializers.ProjectSerializer
    permission_classes = (permissions.ProjectPermission, )
    filter_backends = (filters.CanViewProjectObjFilterBackend,)

    def get_queryset(self):
        qs = models.Project.objects.all()
        return attach_votescount_to_queryset(qs, as_field="stars_count")

    @detail_route(methods=['get'])
    def stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'stats', project)
        return Response(services.get_stats_for_project(project))

    @detail_route(methods=['post'])
    def star(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'star', project)
        votes_service.add_vote(project, user=request.user)
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def unstar(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'unstar', project)
        votes_service.remove_vote(project, user=request.user)
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def issues_stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'issues_stats', project)
        return Response(services.get_stats_for_project_issues(project))

    @detail_route(methods=['get'])
    def issue_filters_data(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'issues_filters_data', project)
        return Response(services.get_issues_filters_data(project))

    @detail_route(methods=['get'])
    def tags(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'tags', project)
        return Response(services.get_all_tags(project))

    @detail_route(methods=['get'])
    def fans(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'fans', project)

        voters = votes_service.get_voters(project)
        voters_data = votes_serializers.VoterSerializer(voters, many=True)
        return Response(voters_data.data)

    @detail_route(methods=["POST"])
    def create_template(self, request, **kwargs):
        template_name = request.DATA.get('template_name', None)
        template_description = request.DATA.get('template_description', None)

        if not template_name:
            raise ParseError("Not valid template name")

        if not template_description:
            raise ParseError("Not valid template description")

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
        return Response(serializers.ProjectTemplateSerializer(template).data, status=201)

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        # TODO REFACTOR THIS
        if not obj.id:
            obj.template = self.request.QUERY_PARAMS.get('template', None)

        super().pre_save(obj)


class MembershipViewSet(ModelCrudViewSet):
    model = models.Membership
    serializer_class = serializers.MembershipSerializer
    permission_classes = (permissions.MembershipPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project", "role")

    def create(self, request, *args, **kwargs):
        data = request.DATA
        data.update({"invited_by_id": request.user.id})
        serializer = self.get_serializer(data=data, files=request.FILES)

        if serializer.is_valid():
            project_id = serializer.data["project"]
            project = get_object_or_404(models.Project, id=project_id)

            self.check_permissions(request, 'create', project)

            qs = self.model.objects.filter(Q(project_id=project_id,
                                             user__email=serializer.data["email"]) |
                                           Q(project_id=project_id,
                                             email=serializer.data["email"]))
            if qs.count() > 0:
                raise exc.WrongArguments(_("Email address is already taken."))

            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        project_id = request.DATA.get('projectId', None)
        if project_id is None:
            raise exc.BadRequest(_('projectId parameter is mandatory'))

        bulk_members = request.DATA.get('bulk_memberships', None)
        if bulk_members is None:
            raise exc.BadRequest(_('bulk_memberships parameter is mandatory'))

        project = get_object_or_404(models.Project, id=project_id)
        members = services.create_members_in_bulk(bulk_members, callback=self.post_save,
                                                  project=project)

        members_serialized = self.serializer_class(members, many=True)
        return Response(data=members_serialized.data)

    @detail_route(methods=["POST"])
    def resend_invitation(self, request, **kwargs):
        services.send_invitation(invitation=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def pre_save(self, object):
        # Only assign new token if a current token value is empty.
        if not object.token:
            object.token = str(uuid.uuid1())

        object.user = services.find_invited_user(object, default=object.user)

        super().pre_save(object)

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


class RolesViewSet(ModelCrudViewSet):
    model = Role
    serializer_class = serializers.RoleSerializer
    permission_classes = (permissions.RolesPermission, )
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)


# User Stories commin ViewSets

class BulkUpdateOrderMixin(object):
    """
    This mixin need three fields in the child class:

    - bulk_update_param: that the name of the field of the data received from
      the cliente that contains the pairs (id, order) to sort the objects.
    - bulk_update_perm: that containts the codename of the permission needed to sort.
    - bulk_update_order: method with bulk update order logic
    """

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        bulk_data = request.DATA.get(self.bulk_update_param, None)

        if bulk_data is None:
            raise exc.BadRequest(_("%s parameter is mandatory") % self.bulk_update_param)

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter is mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        self.check_permissions(request, 'bulk_update_order', project)

        self.__class__.bulk_update_order_action(project, request.user, bulk_data)
        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class PointsViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Points
    serializer_class = serializers.PointsSerializer
    permission_classes = (permissions.PointsPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_points"
    bulk_update_perm = "change_points"
    bulk_update_order_action = services.bulk_update_points_order


class UserStoryStatusViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    permission_classes = (permissions.UserStoryStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_userstory_statuses"
    bulk_update_perm = "change_userstorystatus"
    bulk_update_order_action = services.bulk_update_userstory_status_order


class TaskStatusViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    permission_classes = (permissions.TaskStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_task_statuses"
    bulk_update_perm = "change_taskstatus"
    bulk_update_order_action = services.bulk_update_task_status_order


class SeverityViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Severity
    serializer_class = serializers.SeveritySerializer
    permission_classes = (permissions.SeverityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_severities"
    bulk_update_perm = "change_severity"
    bulk_update_order_action = services.bulk_update_severity_order


class PriorityViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Priority
    serializer_class = serializers.PrioritySerializer
    permission_classes = (permissions.PriorityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_priorities"
    bulk_update_perm = "change_priority"
    bulk_update_order_action = services.bulk_update_priority_order


class IssueTypeViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueType
    serializer_class = serializers.IssueTypeSerializer
    permission_classes = (permissions.IssueTypePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_types"
    bulk_update_perm = "change_issuetype"
    bulk_update_order_action = services.bulk_update_issue_type_order


class IssueStatusViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueStatus
    serializer_class = serializers.IssueStatusSerializer
    permission_classes = (permissions.IssueStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_statuses"
    bulk_update_perm = "change_issuestatus"
    bulk_update_order_action = services.bulk_update_issue_status_order


class ProjectTemplateViewSet(ModelCrudViewSet):
    model = models.ProjectTemplate
    serializer_class = serializers.ProjectTemplateSerializer
    permission_classes = (permissions.ProjectTemplatePermission,)

    def get_queryset(self):
        return models.ProjectTemplate.objects.all()
