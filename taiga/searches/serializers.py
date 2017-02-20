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
