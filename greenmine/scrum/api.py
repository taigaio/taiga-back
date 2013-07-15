# -*- coding: utf-8 -*-

from django.db.models import Q

import django_filters
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from greenmine.scrum.serializers import *
from greenmine.scrum.models import *
from greenmine.scrum.permissions import *


class UserStoryFilter(django_filters.FilterSet):
    no_milestone = django_filters.NumberFilter(name="milestone", lookup_type='isnull')

    class Meta:
        model = UserStory
        fields = ['project', 'milestone', 'no_milestone']


class SimpleFilterMixin(object):
    filter_fields = []
    filter_special_fields = []

    _special_values_dict = {
        'true': True,
        'false': False,
        'null': None,
    }

    def get_queryset(self):
        queryset = super(SimpleFilterMixin, self).get_queryset()
        query_params = {}

        for field_name in self.filter_fields:
            if field_name in self.request.QUERY_PARAMS:
                field_data = self.request.QUERY_PARAMS[field_name]
                if field_data in self._special_values_dict:
                    query_params[field_name] = self._special_values_dict[field_data]
                else:
                    query_params[field_name] = field_data

        if query_params:
            queryset = queryset.filter(**query_params)

        return queryset


class ProjectList(generics.ListCreateAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        )

    def pre_save(self, obj):
        obj.owner = self.request.user


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, ProjectDetailPermission,)


class MilestoneList(generics.ListCreateAPIView):
    model = Milestone
    serializer_class = MilestoneSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user


class MilestoneDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Milestone
    serializer_class = MilestoneSerializer
    permission_classes = (IsAuthenticated, MilestoneDetailPermission,)


class UserStoryList(generics.ListCreateAPIView):
    model = UserStory
    serializer_class = UserStorySerializer
    filter_class = UserStoryFilter
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user


class UserStoryDetail(generics.RetrieveUpdateDestroyAPIView):
    model = UserStory
    serializer_class = UserStorySerializer
    permission_classes = (IsAuthenticated, UserStoryDetailPermission,)


class AttachmentFilter(django_filters.FilterSet):
    class Meta:
        model = Attachment
        fields = ['project', 'object_id']


class IssuesAttachmentList(generics.ListCreateAPIView):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = AttachmentFilter

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(Issue)
        return super(IssuesAttachmentList, self).get_queryset()\
                    .filter(project__members=self.request.user)\
                    .filter(content_type=ct)

    def pre_save(self, obj):
        obj.content_type = ContentType.objects.get_for_model(Issue)
        obj.owner = self.request.user


class IssuesAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentDetailPermission,)


class TasksAttachmentList(generics.ListCreateAPIView):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = AttachmentFilter

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(Task)
        return super(TasksAttachmentList, self).get_queryset()\
                    .filter(project__members=self.request.user)\
                    .filter(content_type=ct)

    def pre_save(self, obj):
        obj.content_type = ContentType.objects.get_for_model(Task)
        obj.owner = self.request.user


class TasksAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentDetailPermission,)


class TaskList(generics.ListCreateAPIView):
    model = Task
    serializer_class = TaskSerializer
    filter_fields = ('user_story', 'milestone', 'project')
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user
        obj.milestone = obj.user_story.milestone


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Task
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, TaskDetailPermission,)

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])


class IssueList(generics.ListCreateAPIView):
    model = Issue
    serializer_class = IssueSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def pre_save(self, obj):
        obj.owner = self.request.user

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class IssueDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Issue
    serializer_class = IssueSerializer
    permission_classes = (IsAuthenticated, IssueDetailPermission,)

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])


class SeverityList(generics.ListCreateAPIView):
    model = Severity
    serializer_class = SeveritySerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class SeverityDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Severity
    serializer_class = SeveritySerializer
    permission_classes = (IsAuthenticated, SeverityDetailPermission,)


class IssueStatusList(generics.ListCreateAPIView):
    model = IssueStatus
    serializer_class = IssueStatusSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class IssueStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = IssueStatus
    serializer_class = IssueStatusSerializer
    permission_classes = (IsAuthenticated, IssueStatusDetailPermission,)


class TaskStatusList(SimpleFilterMixin, generics.ListCreateAPIView):
    model = TaskStatus
    serializer_class = TaskStatusSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class TaskStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = TaskStatus
    serializer_class = TaskStatusSerializer
    permission_classes = (IsAuthenticated, TaskStatusDetailPermission,)


class UserStoryStatusList(generics.ListCreateAPIView):
    model = UserStoryStatus
    serializer_class = UserStoryStatusSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class UserStoryStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = UserStoryStatus
    serializer_class = UserStoryStatusSerializer
    permission_classes = (IsAuthenticated, UserStoryStatusDetailPermission,)


class PriorityList(generics.ListCreateAPIView):
    model = Priority
    serializer_class = PrioritySerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class PriorityDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Priority
    serializer_class = PrioritySerializer
    permission_classes = (IsAuthenticated, PriorityDetailPermission,)


class IssueTypeList(generics.ListCreateAPIView):
    model = IssueType
    serializer_class = IssueTypeSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class IssueTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    model = IssueType
    serializer_class = IssueTypeSerializer
    permission_classes = (IsAuthenticated, IssueTypeDetailPermission,)


class PointsList(generics.ListCreateAPIView):
    model = Points
    serializer_class = PointsSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class PointsDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Points
    serializer_class = PointsSerializer
    permission_classes = (IsAuthenticated, PointsDetailPermission,)
