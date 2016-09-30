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
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.userstories.serializers import UserStoryListSerializer


class MilestoneSerializer(WatchedResourceSerializer, serializers.LightSerializer):
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
    watchers = Field()
    user_stories = MethodField()
    total_points = MethodField()
    closed_points = MethodField()

    def get_user_stories(self, obj):
        return UserStoryListSerializer(obj.user_stories.all(), many=True).data

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr

    def get_closed_points(self, obj):
        assert hasattr(obj, "closed_points_attr"), "instance must have a closed_points_attr attribute"
        return obj.closed_points_attr
