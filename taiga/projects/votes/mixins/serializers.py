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


class VoteResourceSerializerMixin(serializers.ModelSerializer):
    is_voter = serializers.SerializerMethodField("get_is_voter")
    total_voters = serializers.SerializerMethodField("get_total_voters")

    def get_is_voter(self, obj):
        # The "is_voted" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "is_voter", False) or False

    def get_total_voters(self, obj):
        # The "total_voters" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_voters", 0) or 0
