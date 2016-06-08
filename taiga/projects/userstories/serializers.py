# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from taiga.base.api import serializers
from taiga.base.api.utils import get_object_or_404
from taiga.base.fields import PickledObjectField
from taiga.base.fields import PgArrayField
from taiga.base.neighbors import NeighborsSerializerMixin
from taiga.base.utils import json

from taiga.projects.milestones.validators import SprintExistsValidator
from taiga.projects.models import Project
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer
from taiga.projects.serializers import BasicUserStoryStatusSerializer
from taiga.mdrender.service import render as mdrender
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.userstories.validators import UserStoryExistsValidator
from taiga.projects.validators import ProjectExistsValidator, UserStoryStatusExistsValidator
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin

from taiga.users.serializers import UserBasicInfoSerializer

from . import models


class RolePointsField(serializers.WritableField):
    def to_native(self, obj):
        return {str(o.role.id): o.points.id for o in obj.all()}

    def from_native(self, obj):
        if isinstance(obj, dict):
            return obj
        return json.loads(obj)


class UserStorySerializer(WatchersValidator, VoteResourceSerializerMixin,
                          EditableWatchedResourceModelSerializer, serializers.ModelSerializer):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)
    points = RolePointsField(source="role_points", required=False)
    total_points = serializers.SerializerMethodField("get_total_points")
    comment = serializers.SerializerMethodField("get_comment")
    milestone_slug = serializers.SerializerMethodField("get_milestone_slug")
    milestone_name = serializers.SerializerMethodField("get_milestone_name")
    origin_issue = serializers.SerializerMethodField("get_origin_issue")
    blocked_note_html = serializers.SerializerMethodField("get_blocked_note_html")
    description_html = serializers.SerializerMethodField("get_description_html")
    status_extra_info = BasicUserStoryStatusSerializer(source="status", required=False, read_only=True)
    assigned_to_extra_info = UserBasicInfoSerializer(source="assigned_to", required=False, read_only=True)
    owner_extra_info = UserBasicInfoSerializer(source="owner", required=False, read_only=True)
    tribe_gig = PickledObjectField(required=False)

    class Meta:
        model = models.UserStory
        depth = 0
        read_only_fields = ('created_date', 'modified_date', 'owner')

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

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class UserStoryListSerializer(UserStorySerializer):
    class Meta:
        model = models.UserStory
        depth = 0
        read_only_fields = ('created_date', 'modified_date')
        exclude = ("description", "description_html")


class UserStoryNeighborsSerializer(NeighborsSerializerMixin, UserStorySerializer):
    def serialize_neighbor(self, neighbor):
        if neighbor:
            return NeighborUserStorySerializer(neighbor).data
        return None


class NeighborUserStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserStory
        fields = ("id", "ref", "subject")
        depth = 0


class UserStoriesBulkSerializer(ProjectExistsValidator, UserStoryStatusExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    bulk_stories = serializers.CharField()


## Order bulk serializers

class _UserStoryOrderBulkSerializer(UserStoryExistsValidator, serializers.Serializer):
    us_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateUserStoriesOrderBulkSerializer(ProjectExistsValidator, UserStoryStatusExistsValidator,
                                           serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_stories = _UserStoryOrderBulkSerializer(many=True)


## Milestone bulk serializers

class _UserStoryMilestoneBulkSerializer(UserStoryExistsValidator, serializers.Serializer):
    us_id = serializers.IntegerField()


class UpdateMilestoneBulkSerializer(ProjectExistsValidator, SprintExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    bulk_stories = _UserStoryMilestoneBulkSerializer(many=True)

    def validate(self, data):
        """
        All the userstories and the milestone are from the same project
        """
        user_story_ids = [us["us_id"] for us in data["bulk_stories"]]
        project = get_object_or_404(Project, pk=data["project_id"])

        if project.user_stories.filter(id__in=user_story_ids).count() != len(user_story_ids):
            raise serializers.ValidationError("all the user stories must be from the same project")

        if project.milestones.filter(id=data["milestone_id"]).count() != 1:
            raise serializers.ValidationError("the milestone isn't valid for the project")

        return data
