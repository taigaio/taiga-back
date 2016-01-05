# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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
from taiga.base.fields import TagsField
from taiga.base.fields import PgArrayField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.validators import ProjectExistsValidator
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.serializers import BasicIssueStatusSerializer
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin

from taiga.users.serializers import UserBasicInfoSerializer

from . import models


class IssueSerializer(WatchersValidator, VoteResourceSerializerMixin, EditableWatchedResourceModelSerializer, serializers.ModelSerializer):
    tags = TagsField(required=False)
    external_reference = PgArrayField(required=False)
    is_closed = serializers.Field(source="is_closed")
    comment = serializers.SerializerMethodField("get_comment")
    generated_user_stories = serializers.SerializerMethodField("get_generated_user_stories")
    blocked_note_html = serializers.SerializerMethodField("get_blocked_note_html")
    description_html = serializers.SerializerMethodField("get_description_html")
    status_extra_info = BasicIssueStatusSerializer(source="status", required=False, read_only=True)
    assigned_to_extra_info = UserBasicInfoSerializer(source="assigned_to", required=False, read_only=True)
    owner_extra_info = UserBasicInfoSerializer(source="owner", required=False, read_only=True)

    class Meta:
        model = models.Issue
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date')

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_generated_user_stories(self, obj):
        return [{
            "id": us.id,
            "ref": us.ref,
            "subject": us.subject,
        } for us in obj.generated_user_stories.all()]

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class IssueListSerializer(IssueSerializer):
    class Meta:
        model = models.Issue
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date')
        exclude=("description", "description_html")


class IssueListSerializer(IssueSerializer):
    class Meta:
        model = models.Issue
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date')
        exclude=("description", "description_html")


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):
    def serialize_neighbor(self, neighbor):
        if neighbor:
            return NeighborIssueSerializer(neighbor).data
        return None


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0


class IssuesBulkSerializer(ProjectExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_issues = serializers.CharField()
