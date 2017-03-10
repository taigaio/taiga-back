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

import random

from django.conf import settings


DEFAULT_PREDEFINED_COLORS = (
    "#fce94f",
    "#edd400",
    "#c4a000",
    "#8ae234",
    "#73d216",
    "#4e9a06",
    "#d3d7cf",
    "#fcaf3e",
    "#f57900",
    "#ce5c00",
    "#729fcf",
    "#3465a4",
    "#204a87",
    "#888a85",
    "#ad7fa8",
    "#75507b",
    "#5c3566",
    "#ef2929",
    "#cc0000",
    "#a40000"
)

PREDEFINED_COLORS = getattr(settings, "PREDEFINED_COLORS", DEFAULT_PREDEFINED_COLORS)


def generate_random_hex_color():
    return "#{:06x}".format(random.randint(0,0xFFFFFF))


def generate_random_predefined_hex_color():
    return random.choice(PREDEFINED_COLORS)

