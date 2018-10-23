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

from django.utils.translation import ugettext_lazy as _


TEXT_TYPE = "text"
MULTILINE_TYPE = "multiline"
RICHTEXT_TYPE = "richtext"
DATE_TYPE = "date"
URL_TYPE = "url"
DROPDOWN_TYPE = "dropdown"
CHECKBOX_TYPE = "checkbox"
NUMBER_TYPE = "number"

TYPES_CHOICES = (
    (TEXT_TYPE, _("Text")),
    (MULTILINE_TYPE, _("Multi-Line Text")),
    (RICHTEXT_TYPE, _("Rich text")),
    (DATE_TYPE, _("Date")),
    (URL_TYPE, _("Url")),
    (DROPDOWN_TYPE, _("Dropdown")),
    (CHECKBOX_TYPE, _("Checkbox")),
    (NUMBER_TYPE, _("Number")),
)
