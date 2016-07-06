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

from django.utils.translation import ugettext as _

from taiga.base.exceptions import ValidationError


class WatchersValidator:
    def validate_watchers(self, attrs, source):
        users = attrs.get(source, [])

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
        member_ids = project.members.values_list("id", flat=True)
        existing_watcher_ids = project.get_watchers().values_list("id", flat=True)
        result = set(users).difference(member_ids).difference(existing_watcher_ids)
        if result:
            raise ValidationError(_("Watchers contains invalid users"))

        return attrs
