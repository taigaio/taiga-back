# -*- coding: utf-8 -*-

from rest_framework import serializers

from taiga.base.serializers import PickleField, NeighborsSerializerMixin
from taiga.projects.serializers import AttachmentSerializer
from taiga.projects.mixins.notifications.serializers import WatcherValidationSerializerMixin
from . import models


class IssueAttachmentSerializer(AttachmentSerializer):
    class Meta(AttachmentSerializer.Meta):
        fields = ("id", "name", "size", "url", "owner", "created_date", "modified_date", )


class IssueSerializer(WatcherValidationSerializerMixin, serializers.ModelSerializer):
    tags = PickleField(required=False)
    is_closed = serializers.Field(source="is_closed")
    comment = serializers.SerializerMethodField("get_comment")
    attachments = IssueAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = models.Issue

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):

    def serialize_neighbor(self, neighbor):
        return NeighborIssueSerializer(neighbor).data


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0
