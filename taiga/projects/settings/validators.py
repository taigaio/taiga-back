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
from django.utils.translation import ugettext as _

from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.projects.settings.utils import get_allowed_sections

from . import models


class UserProjectSettingsValidator(validators.ModelValidator):

    class Meta:
        model = models.UserProjectSettings
        read_only_fields = ('id', 'created_at', 'modified_at', 'project',
                            'user')

    def validate_homepage(self, attrs, source):
        if attrs[source] not in get_allowed_sections(self.object):
            msg = _("You don't have access to this section")
            raise ValidationError(msg)
        return attrs
