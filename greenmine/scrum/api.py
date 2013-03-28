from rest_framework import generics

from greenmine.scrum.serializers import *
from greenmine.scrum.models import *


class ProjectList(generics.ListCreateAPIView):
    model = Project
    serializer_class = ProjectSerializer


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Project
    serializer_class = ProjectSerializer


class MilestoneList(generics.ListCreateAPIView):
    model = Milestone
    serializer_class = MilestoneSerializer
    filter_fields = ('project_id')


class MilestoneDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Milestone
    serializer_class = MilestoneSerializer


class UserStoryList(generics.ListCreateAPIView):
    model = UserStory
    serializer_class = UserStorySerializer
    filter_fields = ('project_id', 'milestone_id')


class UserStoryDetail(generics.RetrieveUpdateDestroyAPIView):
    model = UserStory
    serializer_class = UserStorySerializer


class ChangeList(generics.ListCreateAPIView):
    model = Change
    serializer_class = ChangeSerializer


class ChangeDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Change
    serializer_class = ChangeSerializer


class ChangeAttachmentList(generics.ListCreateAPIView):
    model = ChangeAttachment
    serializer_class = ChangeAttachmentSerializer


class ChangeAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = ChangeAttachment
    serializer_class = ChangeAttachmentSerializer


class TaskList(generics.ListCreateAPIView):
    model = Task
    serializer_class = TaskSerializer
    filter_fields = ('user_story_id', 'milestone_id', 'project_id')


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Task
    serializer_class = TaskSerializer


class SeverityList(generics.ListCreateAPIView):
    model = Severity
    serializer_class = SeveritySerializer
    filter_fields = ('project_id')


class SeverityDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Severity
    serializer_class = SeveritySerializer


class IssueStatusList(generics.ListCreateAPIView):
    model = IssueStatus
    serializer_class = IssueStatusSerializer
    filter_fields = ('project_id')


class IssueStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = IssueStatus
    serializer_class = IssueStatusSerializer


class TaskStatusList(generics.ListCreateAPIView):
    model = TaskStatus
    serializer_class = TaskStatusSerializer
    filter_fields = ('project_id')


class TaskStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = TaskStatus
    serializer_class = TaskStatusSerializer


class UserStoryStatusList(generics.ListCreateAPIView):
    model = UserStoryStatus
    serializer_class = UserStoryStatusSerializer
    filter_fields = ('project_id')


class UserStoryStatusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = UserStoryStatus
    serializer_class = UserStoryStatusSerializer


class PriorityList(generics.ListCreateAPIView):
    model = Priority
    serializer_class = PrioritySerializer
    filter_fields = ('project_id')


class PriorityDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Priority
    serializer_class = PrioritySerializer


class IssueTypeList(generics.ListCreateAPIView):
    model = IssueType
    serializer_class = IssueTypeSerializer
    filter_fields = ('project_id')


class IssueTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    model = IssueType
    serializer_class = IssueTypeSerializer


class PointsList(generics.ListCreateAPIView):
    model = Points
    serializer_class = PointsSerializer
    filter_fields = ('project_id')


class PointsDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Points
    serializer_class = PointsSerializer
