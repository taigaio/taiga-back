# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models

import reversion


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    tags = PickleField(blank=True, default=[])
    comment = serializers.SerializerMethodField("get_comment")
    history = serializers.SerializerMethodField("get_history")

    class Meta:
        model = models.Task

    def get_comment(self, obj):
        return ""

    def get_task_diff(self, old_task_version, new_task_version):
        old_obj = old_task_version.field_dict
        new_obj = new_task_version.field_dict

        diff_dict = {
            "modified_date": new_obj["modified_date"],
            "by": new_task_version.revision.user,
            "comment": new_task_version.revision.comment,
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
            for version in reversed(list(reversion.get_for_object(obj))):
                if current:
                    task_diff = self.get_task_diff(current, version)
                    diff_list.append(task_diff)

                current = version

        return diff_list
