# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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


class FanResourceSerializerMixin(serializers.ModelSerializer):
    is_fan = serializers.SerializerMethodField("get_is_fan")
    total_fans = serializers.SerializerMethodField("get_total_fans")

    def get_is_fan(self, obj):
        # The "is_fan" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "is_fan", False) or False

    def get_total_fans(self, obj):
        # The "total_fans" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_fans", 0) or 0
