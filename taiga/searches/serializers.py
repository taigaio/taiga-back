# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField


class EpicSearchResultsSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()
    status = Field(attr="status_id")
    assigned_to = Field(attr="assigned_to_id")


class UserStorySearchResultsSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()
    status = Field(attr="status_id")
    total_points = MethodField()
    milestone_name = MethodField()
    milestone_slug = MethodField()

    def get_milestone_name(self, obj):
        return obj.milestone.name if obj.milestone else None

    def get_milestone_slug(self, obj):
        return obj.milestone.slug if obj.milestone else None

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), \
            "instance must have a total_points_attr attribute"

        return obj.total_points_attr


class TaskSearchResultsSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()
    status = Field(attr="status_id")
    assigned_to = Field(attr="assigned_to_id")


class IssueSearchResultsSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()
    status = Field(attr="status_id")
    assigned_to = Field(attr="assigned_to_id")


class WikiPageSearchResultsSerializer(serializers.LightSerializer):
    id = Field()
    slug = Field()
