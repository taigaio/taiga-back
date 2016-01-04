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
from taiga.projects.history import services as history_service
from taiga.projects.notifications.mixins import WatchedResourceModelSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.mdrender.service import render as mdrender

from . import models


class WikiPageSerializer(WatchersValidator, WatchedResourceModelSerializer, serializers.ModelSerializer):
    html = serializers.SerializerMethodField("get_html")
    editions = serializers.SerializerMethodField("get_editions")

    class Meta:
        model = models.WikiPage
        read_only_fields = ('modified_date', 'created_date')

    def get_html(self, obj):
        return mdrender(obj.project, obj.content)

    def get_editions(self, obj):
        return history_service.get_history_queryset_by_model_instance(obj).count() + 1  # +1 for creation


class WikiLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WikiLink
        read_only_fields = ('href',)
