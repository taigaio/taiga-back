# -*- coding: utf-8 -*-

from rest_framework import serializers

from taiga.base.serializers import PickleField, NeighborsSerializerMixin
from taiga.projects.serializers import AttachmentSerializer

from . import models


class IssueAttachmentSerializer(AttachmentSerializer):
    class Meta(AttachmentSerializer.Meta):
        fields = ("id", "name", "size", "url", "owner", "created_date", "modified_date", )


class IssueSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    is_closed = serializers.Field(source="is_closed")
    attachments = IssueAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = models.Issue


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):

    def serialize_neighbor(self, neighbor):
        return NeighborIssueSerializer(neighbor).data


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0
