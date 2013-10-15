# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")

    def get_url(self, obj):
        return obj.attached_file.url if obj and obj.attached_file else ""

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "attached_file", "created_date",
                  "modified_date", "object_id", "url")
        read_only_fields = ("owner",)

# User Stories common serializers

class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Points


class UserStoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserStoryStatus


# Task common serializers

class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskStatus


# Issues common serializers

class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Severity


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Priority


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueStatus


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueType


# Questions common serializers

class QuestionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.QuestionStatus


# Projects

class ProjectSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    list_of_milestones = serializers.Field(source="list_of_milestones")
    us_statuses = UserStoryStatusSerializer(many=True, required=False)          # User Stories
    points = PointsSerializer(many=True, required=False)
    task_statuses = TaskStatusSerializer(many=True, required=False)             # Tasks
    priorities = PrioritySerializer(many=True, required=False)                  # Issues
    severities = SeveritySerializer(many=True, required=False)
    issue_statuses = IssueStatusSerializer(many=True, required=False)
    issue_types = IssueTypeSerializer(many=True, required=False)
    #question_statuses = QuestionStatusSerializer(many=True, required=False)    # Questions

    class Meta:
        model = models.Project
        read_only_fields = ("owner",)
