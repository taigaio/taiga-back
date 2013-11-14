# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models

import reversion


class TaskSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False, default=[])
    comment = serializers.SerializerMethodField("get_comment")

    class Meta:
        model = models.Task

    def get_comment(self, obj):
        return ""
