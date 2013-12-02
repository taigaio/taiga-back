# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import viewsets
from rest_framework import status

from djmail.template_mail import MagicMailBuilder

from greenmine.base import filters
from greenmine.base import exceptions as exc
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet, RetrieveModelMixin
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.aggregates.tags import get_all_tags

from . import serializers
from . import models
from . import permissions

from .aggregates import stats
from .aggregates import filters as filters_aggr


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
                       Q(members=self.request.user))
        return qs.distinct()

    def pre_save(self, obj):
        obj.owner = self.request.user

        # Assign site only if it current
        # value is None
        if not obj.site:
            obj.site = self.request.site

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
                raise exc.WrongArguments("Already exist user with specified email address.")

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


class InvitationViewSet(RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Only used by front for get invitation by it token.
    """
    queryset = models.Membership.objects.all()
    serializer_class = serializers.MembershipSerializer
    lookup_field = "token"
    permission_classes = (AllowAny,)


# User Stories commin ViewSets

class PointsViewSet(ModelListViewSet):
    model = models.Points
    serializer_class = serializers.PointsSerializer
    permission_classes = (IsAuthenticated, permissions.PointsPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)


class UserStoryStatusViewSet(ModelListViewSet):
    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ('project',)


# Tasks commin ViewSets

class TaskStatusViewSet(ModelListViewSet):
    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    permission_classes = (IsAuthenticated, permissions.TaskStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


# Issues common ViewSets

class SeverityViewSet(ModelListViewSet):
    model = models.Severity
    serializer_class = serializers.SeveritySerializer
    permission_classes = (IsAuthenticated, permissions.SeverityPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


class PriorityViewSet(ModelListViewSet):
    model = models.Priority
    serializer_class = serializers.PrioritySerializer
    permission_classes = (IsAuthenticated, permissions.PriorityPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


class IssueTypeViewSet(ModelListViewSet):
    model = models.IssueType
    serializer_class = serializers.IssueTypeSerializer
    permission_classes = (IsAuthenticated, permissions.IssueTypePermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


class IssueStatusViewSet(ModelListViewSet):
    model = models.IssueStatus
    serializer_class = serializers.IssueStatusSerializer
    permission_classes = (IsAuthenticated, permissions.IssueStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)


# Questions commin ViewSets

class QuestionStatusViewSet(ModelListViewSet):
    model = models.QuestionStatus
    serializer_class = serializers.QuestionStatusSerializer
    permission_classes = (IsAuthenticated, permissions.QuestionStatusPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)
