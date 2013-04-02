from rest_framework import serializers

from greenmine.scrum.models import *
from picklefield.fields import dbsafe_encode, dbsafe_decode

import json, reversion

class PickleField(serializers.WritableField):
    """
    Pickle objects serializer.
    """
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Points
        fields = ()


class ProjectSerializer(serializers.ModelSerializer):
    tags = PickleField()

    class Meta:
        model = Project
        fields = ()


class UserStorySerializer(serializers.ModelSerializer):
    tags = PickleField()
    is_closed = serializers.Field(source='is_closed')

    class Meta:
        model = UserStory
        fields = ()
        depth = 0


class MilestoneSerializer(serializers.ModelSerializer):
    user_stories = UserStorySerializer(many=True, required=False)

    class Meta:
        model = Milestone
        fields = ()


class ChangeSerializer(serializers.ModelSerializer):
    tags = PickleField()

    class Meta:
        model = Change
        fields = ()


class ChangeAttachmentSerializer(serializers.ModelSerializer):
    tags = PickleField()

    class Meta:
        model = ChangeAttachment
        fields = ()


class TaskSerializer(serializers.ModelSerializer):
    tags = PickleField()

    class Meta:
        model = Task
        fields = ()

class BaseIssueSerializer(serializers.ModelSerializer):
    tags = PickleField()
    comment = serializers.SerializerMethodField('get_comment')

    class Meta:
        model = Issue
        fields = ()

    def get_comment(self, obj):
        return ''


class IssueSerializer(BaseIssueSerializer):
    tags = PickleField()
    comment = serializers.SerializerMethodField('get_comment')
    history = serializers.SerializerMethodField('get_history')

    def get_issues_diff(self, old_data, new_data, by, comment):

        diff_dict = {
            'modified_date': new_data['modified_date'],
            'by': by,
            'comment': comment,
        }

        for key in old_data.keys():
            if key in ['modified_date', 'created_date', 'comment']:
                continue

            if old_data[key] == new_data[key]:
                continue

            diff_dict[key] = {
                'old': old_data[key],
                'new': new_data[key],
            }

        return diff_dict

    def get_history(self, obj):
        diff_list = []
        current_data = BaseIssueSerializer(obj).data

        for version in reversed(list(reversion.get_for_object(obj))):
            version_data = version.field_dict
            by = version.revision.user
            comment = version.revision.comment
            issues_diff = self.get_issues_diff(current_data, version_data, by, comment)
            diff_list.append(issues_diff)
            current_data = version.field_dict

        return diff_list


class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Severity
        fields = ()


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ()


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ()


class UserStoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStoryStatus
        fields = ()


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ()


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ()


