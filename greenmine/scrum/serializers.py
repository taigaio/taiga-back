from rest_framework import serializers

from greenmine.scrum.models import *

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ()


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ()


class UserStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStory
        fields = ()


class ChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        fields = ()


class ChangeAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeAttachment
        fields = ()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ()


class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Severity
        fields = ()


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ()


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ()


class UserStoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStoryStatus
        fields = ()


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ()


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ()


class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Points
        fields = ()
