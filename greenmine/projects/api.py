# -*- coding: utf-8 -*-

from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from greenmine.base import filters
from greenmine.base.api import ModelCrudViewSet, ModelListViewSet
from greenmine.base.notifications.api import NotificationSenderMixin

from . import serializers
from . import models
from . import permissions


class ProjectViewSet(ModelCrudViewSet):
    model = models.Project
    serializer_class = serializers.ProjectDetailSerializer
    list_serializer_class = serializers.ProjectSerializer
    permission_classes = (IsAuthenticated, permissions.ProjectPermission)

    @detail_route(methods=['get'])
    def stats(self, request, pk=None):
        project = get_object_or_404(models.Project, pk=pk)
        project_stats = {
            'name': project.name,
            'total_milestones': project.total_milestones,
            'total_points': project.total_story_points,
            'milestones': []
        }

        current_milestone = 0
        current_evolution = 0
        current_team_increment = 0
        current_client_increment = 0
        optimal_points_per_sprint = project.total_story_points / (project.total_milestones - 1)

        for ml in project.milestones.all():
            optimal_points = project.total_story_points - (optimal_points_per_sprint * current_milestone)
            project_stats['milestones'].append({
                'name': ml.name,
                'optimal': optimal_points,
                'evolution': project.total_story_points - current_evolution,
                'team-increment': current_team_increment,
                'client-increment': current_client_increment,
            })
            current_milestone += 1
            current_evolution += sum(ml.closed_points.values())
            current_team_increment += sum(ml.team_increment_points.values())
            current_client_increment += sum(ml.client_increment_points.values())

        if project.total_milestones > project.milestones.all().count():
            for x in range(project.milestones.all().count(), project.total_milestones):
                optimal_points = project.total_story_points - (optimal_points_per_sprint * current_milestone)
                if current_evolution is not None:
                    current_evolution = project.total_story_points - current_evolution
                project_stats['milestones'].append({
                    'name': "Future sprint",
                    'optimal': optimal_points,
                    'evolution': current_evolution,
                    'team-increment': current_team_increment + sum(project.future_team_increment.values()),
                    'client-increment': current_client_increment + sum(project.future_client_increment.values()),
                })
                current_milestone += 1
                current_evolution = None

        return Response(project_stats)

    def get_queryset(self):
        qs = super(ProjectViewSet, self).get_queryset()
        qs = qs.filter(Q(owner=self.request.user) |
                       Q(members=self.request.user))
        return qs.distinct()

    def pre_save(self, obj):
        obj.owner = self.request.user
        super(ProjectViewSet, self).pre_save(obj)


class MembershipViewSet(ModelCrudViewSet):
    model = models.Membership
    serializer_class = serializers.MembershipSerializer
    permission_classes = (IsAuthenticated, permissions.MembershipPermission)


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


# Issues commin ViewSets

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
