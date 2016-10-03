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
from taiga.base.fields import Field, MethodField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.mixins.serializers import OwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import AssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import StatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.tagging.serializers import TaggedInProjectResourceSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin


class IssueListSerializer(VoteResourceSerializerMixin, WatchedResourceSerializer,
                          OwnerExtraInfoSerializerMixin, AssignedToExtraInfoSerializerMixin,
                          StatusExtraInfoSerializerMixin,
                          TaggedInProjectResourceSerializer, serializers.LightSerializer):
    id = Field()
    ref = Field()
    severity = Field(attr="severity_id")
    priority = Field(attr="priority_id")
    type = Field(attr="type_id")
    milestone = Field(attr="milestone_id")
    project = Field(attr="project_id")
    created_date = Field()
    modified_date = Field()
    finished_date = Field()
    subject = Field()
    external_reference = Field()
    version = Field()
    watchers = Field()
    is_blocked = Field()
    blocked_note = Field()
    is_closed = Field()


class IssueSerializer(IssueListSerializer):
    comment = MethodField()
    generated_user_stories = MethodField()
    blocked_note_html = MethodField()
    description = Field()
    description_html = MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_generated_user_stories(self, obj):
        assert hasattr(obj, "generated_user_stories_attr"), "instance must have a generated_user_stories_attr attribute"
        return obj.generated_user_stories_attr

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):
    pass
