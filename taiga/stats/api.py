# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from collections import OrderedDict

from django.conf import settings
from django.views.decorators.cache import cache_page

from taiga.base import response
from taiga.base.api import viewsets

from . import permissions
from . import services


CACHE_TIMEOUT = getattr(settings, "STATS_CACHE_TIMEOUT", 0)


class BaseStatsViewSet(viewsets.ViewSet):
    @property
    def _cache_timeout(self):
        return CACHE_TIMEOUT

    def dispatch(self, *args, **kwargs):
        return cache_page(self._cache_timeout)(super().dispatch)(*args, **kwargs)


class SystemStatsViewSet(BaseStatsViewSet):
    permission_classes = (permissions.SystemStatsPermission,)

    def list(self, request, **kwargs):
        stats = OrderedDict()
        stats["users"] = services.get_users_public_stats()
        stats["projects"] = services.get_projects_public_stats()
        stats["userstories"] = services.get_user_stories_public_stats()
        return response.Ok(stats)


class DiscoverStatsViewSet(BaseStatsViewSet):
    permission_classes = (permissions.DiscoverStatsPermission,)

    def list(self, request, **kwargs):
        stats = OrderedDict()
        stats["projects"] = services.get_projects_discover_stats(user=request.user)
        return response.Ok(stats)
