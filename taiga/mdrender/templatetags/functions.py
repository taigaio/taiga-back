# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from django_jinja import library
from jinja2 import Markup
from taiga.mdrender.service import render


@library.global_function
def mdrender(project, text) -> str:
    if text:
        return Markup(render(project, text))
    return ""
