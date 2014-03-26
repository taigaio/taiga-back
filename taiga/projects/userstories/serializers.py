# -*- coding: utf-8 -*-

import json
from django.db.models import get_model
from rest_framework import serializers

from taiga.base.serializers import PickleField, NeighborsSerializerMixin

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
    points = RolePointsField(source="role_points", required=False)
    total_points = serializers.SerializerMethodField("get_total_points")
    comment = serializers.SerializerMethodField("get_comment")
    milestone_slug = serializers.SerializerMethodField("get_milestone_slug")
    milestone_name = serializers.SerializerMethodField("get_milestone_name")
    origin_issue = serializers.SerializerMethodField("get_origin_issue")

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
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_milestone_slug(self, obj):
        if obj.milestone:
            return obj.milestone.slug
        else:
            return None

    def get_milestone_name(self, obj):
        if obj.milestone:
            return obj.milestone.name
        else:
            return None

    def get_origin_issue(self, obj):
        if obj.generated_from_issue:
            return {
                "id": obj.generated_from_issue.id,
                "ref": obj.generated_from_issue.ref,
                "subject": obj.generated_from_issue.subject,
            }
        return None


class UserStoryNeighborsSerializer(NeighborsSerializerMixin, UserStorySerializer):

    def serialize_neighbor(self, neighbor):
        return NeighborUserStorySerializer(neighbor).data


class NeighborUserStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserStory
        fields = ("id", "ref", "subject")
        depth = 0
