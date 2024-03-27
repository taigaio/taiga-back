# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from taiga.base import response
from taiga.base.api.viewsets import ReadOnlyListViewSet

from . import permissions


class LocalesViewSet(ReadOnlyListViewSet):
    permission_classes = (permissions.LocalesPermission,)

    def list(self, request, *args, **kwargs):
        locales = [{"code": c, "name": n, "bidi": c in settings.LANGUAGES_BIDI} for c, n in settings.LANGUAGES]
        return response.Ok(locales)
