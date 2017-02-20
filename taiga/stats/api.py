# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Taiga Agile LLC <support@taiga.io>
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
