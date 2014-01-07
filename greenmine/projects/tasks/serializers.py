# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models

import reversion


class TaskSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False, default=[])
    comment = serializers.SerializerMethodField("get_comment")
    milestone_slug = serializers.SerializerMethodField("get_milestone_slug")

    class Meta:
        model = models.Task

    def get_comment(self, obj):
        return ""

    def get_milestone_slug(self, obj):
        if obj.milestone:
            return obj.milestone.slug
        else:
            return None
