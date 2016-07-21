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
from taiga.projects.attachments.serializers import BasicAttachmentsInfoSerializerMixin
from taiga.projects.mixins.serializers import OwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import AssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import StatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin


class OriginIssueSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


class UserStoryListSerializer(
        VoteResourceSerializerMixin, WatchedResourceSerializer,
        OwnerExtraInfoSerializerMixin, AssignedToExtraInfoSerializerMixin,
        StatusExtraInfoSerializerMixin, BasicAttachmentsInfoSerializerMixin,
        serializers.LightSerializer):

    id = Field()
    ref = Field()
    milestone = Field(attr="milestone_id")
    milestone_slug = MethodField()
    milestone_name = MethodField()
    project = Field(attr="project_id")
    is_closed = Field()
    points = MethodField()
    backlog_order = Field()
    sprint_order = Field()
    kanban_order = Field()
    created_date = Field()
    modified_date = Field()
    finish_date = Field()
    subject = Field()
    client_requirement = Field()
    team_requirement = Field()
    generated_from_issue = Field(attr="generated_from_issue_id")
    external_reference = Field()
    tribe_gig = Field()
    version = Field()
    watchers = Field()
    is_blocked = Field()
    blocked_note = Field()
    tags = Field()
    total_points = MethodField()
    comment = MethodField()
    origin_issue = OriginIssueSerializer(attr="generated_from_issue")

    tasks = MethodField()

    def get_milestone_slug(self, obj):
        return obj.milestone.slug if obj.milestone else None

    def get_milestone_name(self, obj):
        return obj.milestone.name if obj.milestone else None

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr

    def get_points(self, obj):
        assert hasattr(obj, "role_points_attr"), "instance must have a role_points_attr attribute"
        if obj.role_points_attr is None:
            return {}

        return obj.role_points_attr

    def get_comment(self, obj):
        return ""

    def get_tasks(self, obj):
        include_tasks = getattr(obj, "include_tasks", False)

        if include_tasks:
            assert hasattr(obj, "tasks_attr"), "instance must have a tasks_attr attribute"

        if not include_tasks or obj.tasks_attr is None:
            return []

        return obj.tasks_attr


class UserStorySerializer(UserStoryListSerializer):
    comment = MethodField()
    blocked_note_html = MethodField()
    description = Field()
    description_html = MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class UserStoryNeighborsSerializer(NeighborsSerializerMixin, UserStorySerializer):
    pass
