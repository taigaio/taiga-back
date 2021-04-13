# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.userstories.serializers import UserStoryNestedSerializer
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin


class MilestoneSerializer(ProjectExtraInfoSerializerMixin,
                          serializers.LightSerializer):
    id = Field()
    name = Field()
    slug = Field()
    owner = Field(attr="owner_id")
    project = Field(attr="project_id")
    estimated_start = Field()
    estimated_finish = Field()
    created_date = Field()
    modified_date = Field()
    closed = Field()
    disponibility = Field()
    order = Field()
    user_stories = MethodField()
    total_points = MethodField()
    closed_points = MethodField()

    def get_user_stories(self, obj):
        return UserStoryNestedSerializer(obj.user_stories.all(), many=True).data

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr

    def get_closed_points(self, obj):
        assert hasattr(obj, "closed_points_attr"), "instance must have a closed_points_attr attribute"
        return obj.closed_points_attr
