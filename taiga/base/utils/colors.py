# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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

