# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")

    def get_url(self, obj):
        # FIXME: add sites or correct url.
        if obj.attached_file:
            return "http://localhost:8000{0}".format(obj.attached_file.url)
        return None

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "attached_file",
                  "created_date", "object_id", "url")
        read_only_fields = ("owner",)
        fields = ()


class ProjectSerializer(serializers.ModelSerializer):
    tags = PickleField()
    list_of_milestones = serializers.Field(source="list_of_milestones")

    class Meta:
        model = models.Project


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
