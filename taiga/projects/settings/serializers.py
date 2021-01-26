# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from . import models

from taiga.projects.settings.utils import get_allowed_sections


class UserProjectSettingsSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField("get_project_name")
    allowed_sections = serializers.SerializerMethodField("get_allowed_sections")

    class Meta:
        model = models.UserProjectSettings
        fields = ('id', 'project', 'project_name', 'homepage', 'allowed_sections')

    def get_project_name(self, obj):
        return obj.project.name

    def get_allowed_sections(self, obj):
        return get_allowed_sections(obj)
