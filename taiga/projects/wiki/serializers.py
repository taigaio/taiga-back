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
from taiga.projects.history import services as history_service
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.mdrender.service import render as mdrender


class WikiPageSerializer(
    WatchedResourceSerializer, ProjectExtraInfoSerializerMixin,
    serializers.LightSerializer
):
    id = Field()
    project = Field(attr="project_id")
    slug = Field()
    content = Field()
    owner = Field(attr="owner_id")
    last_modifier = Field(attr="last_modifier_id")
    created_date = Field()
    modified_date = Field()

    html = MethodField()
    editions = MethodField()

    version = Field()

    def get_html(self, obj):
        return mdrender(obj.project, obj.content)

    def get_editions(self, obj):
        return history_service.get_history_queryset_by_model_instance(obj).count() + 1  # +1 for creation


class WikiLinkSerializer(serializers.LightSerializer):
    id = Field()
    project = Field(attr="project_id")
    title = Field()
    href = Field()
    order = Field()
