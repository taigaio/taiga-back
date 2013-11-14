# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models

import reversion


class IssueSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    comment = serializers.SerializerMethodField("get_comment")
    is_closed = serializers.Field(source="is_closed")

    class Meta:
        model = models.Issue

    def get_comment(self, obj):
        return ""
