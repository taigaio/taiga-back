# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class WatchersValidator:
    def validate_watchers(self, attrs, source):
        users = attrs[source]

        # Try obtain a valid project
        if self.object is None and "project" in attrs:
            project = attrs["project"]
        elif self.object:
            project = self.object.project
        else:
            project = None

        # If project is empty in all conditions, continue
        # without errors, because other validator should
        # validate the empty project field.
        if not project:
            return attrs

        # Check if incoming watchers are contained
        # in project members list
        result = set(users).difference(set(project.members.all()))
        if result:
            raise serializers.ValidationError("Watchers contains invalid users")

        return attrs
