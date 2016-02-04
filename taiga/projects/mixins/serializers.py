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

from django.utils.translation import ugettext as _

class ValidateDuplicatedNameInProjectMixin(serializers.ModelSerializer):

    def validate_name(self, attrs, source):
        """
        Check the points name is not duplicated in the project on creation
        """
        model = self.opts.model
        qs = None
        # If the object exists:
        if self.object and attrs.get(source, None):
            qs = model.objects.filter(project=self.object.project, name=attrs[source]).exclude(id=self.object.id)

        if not self.object and attrs.get("project", None)  and attrs.get(source, None):
            qs = model.objects.filter(project=attrs["project"], name=attrs[source])

        if qs and qs.exists():
              raise serializers.ValidationError(_("Name duplicated for the project"))

        return attrs
