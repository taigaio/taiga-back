# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from taiga.base.utils.thumbnails import get_thumbnail_url


def get_logo_small_thumbnail_url(project):
    if project.logo:
        return get_thumbnail_url(project.logo, settings.THN_LOGO_SMALL)
    return None


def get_logo_big_thumbnail_url(project):
    if project.logo:
        return get_thumbnail_url(project.logo, settings.THN_LOGO_BIG)
    return None
