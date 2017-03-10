# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from taiga.base.fields import Field, MethodField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.attachments.serializers import BasicAttachmentsInfoSerializerMixin
from taiga.projects.mixins.serializers import OwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import AssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import StatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.tagging.serializers import TaggedInProjectResourceSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin


class EpicListSerializer(VoteResourceSerializerMixin, WatchedResourceSerializer,
                         OwnerExtraInfoSerializerMixin, AssignedToExtraInfoSerializerMixin,
                         StatusExtraInfoSerializerMixin, ProjectExtraInfoSerializerMixin,
                         BasicAttachmentsInfoSerializerMixin,
                         TaggedInProjectResourceSerializer, serializers.LightSerializer):

    id = Field()
    ref = Field()
    project = Field(attr="project_id")
    created_date = Field()
    modified_date = Field()
    subject = Field()
    color = Field()
    epics_order = Field()
    client_requirement = Field()
    team_requirement = Field()
    version = Field()
    watchers = Field()
    is_blocked = Field()
    blocked_note = Field()
    is_closed = MethodField()
    user_stories_counts = MethodField()

    def get_is_closed(self, obj):
        return obj.status is not None and obj.status.is_closed

    def get_user_stories_counts(self, obj):
        assert hasattr(obj, "user_stories_counts"), "instance must have a user_stories_counts attribute"
        return obj.user_stories_counts


class EpicSerializer(EpicListSerializer):
    comment = MethodField()
    blocked_note_html = MethodField()
    description = Field()
    description_html = MethodField()

    def get_comment(self, obj):
        return ""

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class EpicNeighborsSerializer(NeighborsSerializerMixin, EpicSerializer):
    pass


class EpicRelatedUserStorySerializer(serializers.LightSerializer):
    epic = Field(attr="epic_id")
    user_story = Field(attr="user_story_id")
    order = Field()
