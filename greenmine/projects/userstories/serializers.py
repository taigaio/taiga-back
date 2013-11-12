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
    history = serializers.SerializerMethodField("get_history")

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

    def get_user_stories_diff(self, old_us_version, new_us_version):
        old_obj = old_us_version.field_dict
        new_obj = new_us_version.field_dict

        diff_dict = {
            "modified_date": new_obj["modified_date"],
            "by": new_us_version.revision.user,
            "comment": new_us_version.revision.comment,
        }

        for key in old_obj.keys():
            if key == "modified_date":
                continue

            if old_obj[key] == new_obj[key]:
                continue

            diff_dict[key] = {
                "old": old_obj[key],
                "new": new_obj[key],
            }

        return diff_dict

    def get_history(self, obj):
        diff_list = []
        current = None

        if obj:
            for version in reversion.get_for_object(obj).order_by("revision__date_created"):
                if current:
                    us_diff = self.get_user_stories_diff(current, version)
                    diff_list.append(us_diff)

                current = version

        return diff_list
