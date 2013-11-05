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
            'milestones': self._milestones_stats(project)
        }
        return Response(project_stats)

    def _milestones_stats(self, project):
        current_evolution = 0
        current_team_increment = 0
        current_client_increment = 0
        optimal_points_per_sprint = project.total_story_points / (project.total_milestones)
        future_team_increment = sum(project.future_team_increment.values())
        future_client_increment = sum(project.future_client_increment.values())

        milestones = project.milestones.order_by('estimated_start')

        for current_milestone in range(0, max(milestones.count(), project.total_milestones)):
            optimal_points = project.total_story_points - (optimal_points_per_sprint * current_milestone)
            evolution = project.total_story_points - current_evolution if current_evolution is not None else None

            if current_milestone < milestones.count():
                ml = milestones[current_milestone]
                milestone_name = ml.name
                team_increment = current_team_increment
                client_increment = current_client_increment

                current_evolution += sum(ml.closed_points.values())
                current_team_increment += sum(ml.team_increment_points.values())
                current_client_increment += sum(ml.client_increment_points.values())
            else:
                milestone_name = "Future sprint"
                team_increment = current_team_increment + future_team_increment,
                client_increment = current_client_increment + future_client_increment,
                current_evolution = None

            yield {
                'name': milestone_name,
                'optimal': optimal_points,
                'evolution': evolution,
                'team-increment': team_increment,
                'client-increment': client_increment,
            }
        optimal_points -= optimal_points_per_sprint
        yield {
            'name': 'Project End',
            'optimal': optimal_points,
            'evolution': evolution,
            'team-increment': team_increment,
            'client-increment': client_increment,
        }

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
