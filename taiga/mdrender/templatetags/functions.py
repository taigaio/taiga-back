# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django_jinja import library
from jinja2.utils import markupsafe
from taiga.mdrender.service import render


@library.global_function
def mdrender(project, text) -> str:
    if text:
        return markupsafe.Markup(render(project, text))
    return ""
