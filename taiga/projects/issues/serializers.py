# -*- coding: utf-8 -*-

from rest_framework import serializers

from taiga.base.serializers import PickleField, NeighborsSerializerMixin

from . import models


class IssueSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    comment = serializers.SerializerMethodField("get_comment")
    is_closed = serializers.Field(source="is_closed")

    class Meta:
        model = models.Issue

    def get_comment(self, obj):
        return ""


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):

    def serialize_neighbor(self, neighbor):
        return NeighborIssueSerializer(neighbor).data


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0
