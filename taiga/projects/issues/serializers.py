# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from rest_framework import serializers

from taiga.base.serializers import PickleField, NeighborsSerializerMixin
from taiga.projects.serializers import AttachmentSerializer
from taiga.projects.mixins.notifications.serializers import WatcherValidationSerializerMixin

from . import models


class IssueAttachmentSerializer(AttachmentSerializer):
    class Meta(AttachmentSerializer.Meta):
        fields = ("id", "name", "size", "url", "owner", "created_date", "modified_date", )


class IssueSerializer(WatcherValidationSerializerMixin, serializers.ModelSerializer):
    tags = PickleField(required=False)
    is_closed = serializers.Field(source="is_closed")
    comment = serializers.SerializerMethodField("get_comment")
    attachments = IssueAttachmentSerializer(many=True, read_only=True)
    generated_user_stories = serializers.SerializerMethodField("get_generated_user_stories")

    class Meta:
        model = models.Issue

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_generated_user_stories(self, obj):
        return obj.generated_user_stories.values("id", "ref", "subject")


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):

    def serialize_neighbor(self, neighbor):
        return NeighborIssueSerializer(neighbor).data


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0
