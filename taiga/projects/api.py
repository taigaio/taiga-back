# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status

from djmail.template_mail import MagicMailBuilder

from taiga.domains import get_active_domain
from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route, detail_route
from taiga.base.permissions import has_project_perm
from taiga.base.api import ModelCrudViewSet, ModelListViewSet, RetrieveModelMixin
from taiga.base.users.models import Role
from taiga.base.notifications.api import NotificationSenderMixin
from taiga.projects.aggregates.tags import get_all_tags

from . import serializers
from . import models
from . import permissions
from . import services

from .aggregates import stats
from .aggregates import filters as filters_aggr


class ProjectAdminViewSet(ModelCrudViewSet):
    model = models.Project
    serializer_class = serializers.ProjectDetailSerializer
    list_serializer_class = serializers.ProjectSerializer
    permission_classes = (IsAuthenticated, permissions.ProjectAdminPermission)

    def get_queryset(self):
        domain = get_active_domain()
        return domain.projects.all()

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        # TODO REFACTOR THIS
        if not obj.id:
            obj.template = self.request.QUERY_PARAMS.get('template', None)

        # FIXME

        # Assign domain only if it current
        # value is None
        if not obj.domain:
            obj.domain = self.request.domain

        super().pre_save(obj)


class ProjectViewSet(ModelCrudViewSet):
    model = models.Project
    serializer_class = serializers.ProjectDetailSerializer
    list_serializer_class = serializers.ProjectSerializer
    permission_classes = (IsAuthenticated, permissions.ProjectPermission)

    @detail_route(methods=['get'])
    def stats(self, request, pk=None):
        project = self.get_object()
        return Response(stats.get_stats_for_project(project))

    @detail_route(methods=['get'])
    def issues_stats(self, request, pk=None):
        project = self.get_object()
        return Response(stats.get_stats_for_project_issues(project))

    @detail_route(methods=['get'])
    def issue_filters_data(self, request, pk=None):
        project = self.get_object()
        return Response(filters_aggr.get_issues_filters_data(project))

    @detail_route(methods=['get'])
    def tags(self, request, pk=None):
        project = self.get_object()
        return Response(get_all_tags(project))

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(Q(owner=self.request.user) |
                       Q(members=self.request.user)).filter(domain=get_active_domain())
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        # FIXME

        # Assign domain only if it current
        # value is None
        if not obj.domain:
            obj.domain = self.request.domain

        super().pre_save(obj)


class MembershipViewSet(ModelCrudViewSet):
    model = models.Membership
    serializer_class = serializers.MembershipSerializer
    permission_classes = (IsAuthenticated, permissions.MembershipPermission)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            qs = self.model.objects.filter(Q(project_id=serializer.data["project"],
                                             user__email=serializer.data["email"]) |
                                           Q(project_id=serializer.data["project"],
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

    def pre_save(self, object):
        # Only assign new token if a current token value is empty.
        if not object.token:
            object.token = str(uuid.uuid1())

        super().pre_save(object)

    def post_save(self, object, created=False):
        super().post_save(object, created=created)

        if not created:
            return

        # Send email only if a new membership is created
        mbuilder = MagicMailBuilder()
        email = mbuilder.membership_invitation(object.email, {"membership": object})
        email.send()


class InvitationViewSet(RetrieveModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    Only used by front for get invitation by it token.
    """
    queryset = models.Membership.objects.all()
    serializer_class = serializers.MembershipSerializer
    lookup_field = "token"
    permission_classes = (AllowAny,)

    def list(self, *args, **kwargs):
        raise exc.PermissionDenied(_("You don't have permisions to see that."))


class RolesViewSet(ModelCrudViewSet):
    model = Role
    serializer_class = serializers.RoleSerializer
    permission_classes = (IsAuthenticated, permissions.RolesPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)

# User Stories commin ViewSets

class PointsViewSet(ModelCrudViewSet):
    model = models.Points
    serializer_class = serializers.PointsSerializer
    permission_classes = (IsAuthenticated, permissions.PointsPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_points should be:
        # [[1,1],[23, 2], ...]

        bulk_points = request.DATA.get("bulk_points", None)

        if bulk_points is None:
            raise exc.BadRequest(_("bulk_points parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_points'):
            raise exc.PermissionDenied(_("You don't have permisions to change points."))

        service = services.PointsService()
        service.bulk_update_order(project, request.user, bulk_points)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class UserStoryStatusViewSet(ModelCrudViewSet):
    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_userstory_statuses should be:
        # [[1,1],[23, 2], ...]

        bulk_userstory_statuses = request.DATA.get("bulk_userstory_statuses", None)

        if bulk_userstory_statuses is None:
            raise exc.BadRequest(_("bulk_userstory_statuses parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_userstorystatus'):
            raise exc.PermissionDenied(_("You don't have permisions to change user_story_statuses."))

        service = services.UserStoryStatusesService()
        service.bulk_update_order(project, request.user, bulk_userstory_statuses)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


# Tasks commin ViewSets

class TaskStatusViewSet(ModelCrudViewSet):
    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    permission_classes = (IsAuthenticated, permissions.TaskStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_task_statuses should be:
        # [[1,1],[23, 2], ...]

        bulk_task_statuses = request.DATA.get("bulk_task_statuses", None)

        if bulk_task_statuses is None:
            raise exc.BadRequest(_("bulk_task_statuses parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_taskstatus'):
            raise exc.PermissionDenied(_("You don't have permisions to change task_statuses."))

        service = services.TaskStatusesService()
        service.bulk_update_order(project, request.user, bulk_task_statuses)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


# Issues common ViewSets

class SeverityViewSet(ModelCrudViewSet):
    model = models.Severity
    serializer_class = serializers.SeveritySerializer
    permission_classes = (IsAuthenticated, permissions.SeverityPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_severities should be:
        # [[1,1],[23, 2], ...]

        bulk_severities = request.DATA.get("bulk_severities", None)

        if bulk_severities is None:
            raise exc.BadRequest(_("bulk_severities parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_severity'):
            raise exc.PermissionDenied(_("You don't have permisions to change severities."))

        service = services.SeveritiesService()
        service.bulk_update_order(project, request.user, bulk_severities)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class PriorityViewSet(ModelCrudViewSet):
    model = models.Priority
    serializer_class = serializers.PrioritySerializer
    permission_classes = (IsAuthenticated, permissions.PriorityPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_priorities should be:
        # [[1,1],[23, 2], ...]

        bulk_priorities = request.DATA.get("bulk_priorities", None)

        if bulk_priorities is None:
            raise exc.BadRequest(_("bulk_priorities parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_priority'):
            raise exc.PermissionDenied(_("You don't have permisions to change priorities."))

        service = services.PrioritiesService()
        service.bulk_update_order(project, request.user, bulk_priorities)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class IssueTypeViewSet(ModelCrudViewSet):
    model = models.IssueType
    serializer_class = serializers.IssueTypeSerializer
    permission_classes = (IsAuthenticated, permissions.IssueTypePermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_issue_types should be:
        # [[1,1],[23, 2], ...]

        bulk_issue_types = request.DATA.get("bulk_issue_types", None)

        if bulk_issue_types is None:
            raise exc.BadRequest(_("bulk_riorities parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_issuetype'):
            raise exc.PermissionDenied(_("You don't have permisions to change issue_types."))

        service = services.IssueTypesService()
        service.bulk_update_order(project, request.user, bulk_issue_types)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class IssueStatusViewSet(ModelCrudViewSet):
    model = models.IssueStatus
    serializer_class = serializers.IssueStatusSerializer
    permission_classes = (IsAuthenticated, permissions.IssueStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_issue_statuses should be:
        # [[1,1],[23, 2], ...]

        bulk_issue_statuses = request.DATA.get("bulk_issue_statuses", None)

        if bulk_issue_statuses is None:
            raise exc.BadRequest(_("bulk_riorities parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_issuestatus'):
            raise exc.PermissionDenied(_("You don't have permisions to change issue_statuses."))

        service = services.IssueStatusesService()
        service.bulk_update_order(project, request.user, bulk_issue_statuses)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


# Questions commin ViewSets

class QuestionStatusViewSet(ModelCrudViewSet):
    model = models.QuestionStatus
    serializer_class = serializers.QuestionStatusSerializer
    permission_classes = (IsAuthenticated, permissions.QuestionStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulk_question_statuses should be:
        # [[1,1],[23, 2], ...]

        bulk_question_statuses = request.DATA.get("bulk_question_statuses", None)

        if bulk_question_statuses is None:
            raise exc.BadRequest(_("bulk_question_statuses parameter is mandatory"))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("project parameter ir mandatory"))

        project = get_object_or_404(models.Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_questionstatus'):
            raise exc.PermissionDenied(_("You don't have permisions to change question_statuses."))

        service = services.QuestionStatusesService()
        service.bulk_update_order(project, request.user, bulk_question_statuses)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)
