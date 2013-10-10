# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models

import reversion


class IssueSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    comment = serializers.SerializerMethodField("get_comment")
    history = serializers.SerializerMethodField("get_history")
    is_closed = serializers.Field(source="is_closed")

    class Meta:
        model = models.Issue

    def get_comment(self, obj):
        # TODO
        return ""

    def get_issues_diff(self, old_issue_version, new_issue_version):
        old_obj = old_issue_version.field_dict
        new_obj = new_issue_version.field_dict

        diff_dict = {
            "modified_date": new_obj["modified_date"],
            "by": old_issue_version.revision.user,
            "comment": old_issue_version.revision.comment,
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
                    issues_diff = self.get_issues_diff(current, version)
                    diff_list.append(issues_diff)

                current = version

        return diff_list
