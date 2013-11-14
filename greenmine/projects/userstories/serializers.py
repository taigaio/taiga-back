# -*- coding: utf-8 -*-

import json, reversion
from django.db.models import get_model
from rest_framework import serializers

from greenmine.base.serializers import PickleField
from . import models


class RolePointsField(serializers.WritableField):
    def to_native(self, obj):
        return {str(o.role.id): o.points.id for o in obj.all()}

    def from_native(self, obj):
        if isinstance(obj, dict):
            return obj
        return json.loads(obj)


class UserStorySerializer(serializers.ModelSerializer):
    tags = PickleField(default=[], required=False)
    is_closed = serializers.Field(source="is_closed")
    points = RolePointsField(source="role_points", required=False )
    total_points = serializers.SerializerMethodField("get_total_points")
    comment = serializers.SerializerMethodField("get_comment")

    class Meta:
        model = models.UserStory
        depth = 0

    def save_object(self, obj, **kwargs):
        role_points = obj._related_data.pop("role_points", None)
        super().save_object(obj, **kwargs)

        points_modelcls = get_model("projects", "Points")

        obj.project.update_role_points()
        if role_points:
            for role_id, points_id in role_points.items():
                role_points = obj.role_points.get(role__id=role_id)
                role_points.points = points_modelcls.objects.get(id=points_id,
                                                                 project=obj.project)
                role_points.save()

    def get_total_points(self, obj):
        return obj.get_total_points()

    def get_comment(self, obj):
        return ""
