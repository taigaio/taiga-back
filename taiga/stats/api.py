# Copyright (C) 2014-2015 Taiga Agile LLC <support@taiga.io>
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

from taiga.base.api import viewsets
from taiga.base import response

from . import permissions
from . import services


class SystemStatsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.SystemStatsPermission,)

    def list(self, request, **kwargs):
        stats = OrderedDict()
        stats["users"] = services.get_users_stats()
        stats["projects"] = services.get_projects_stats()
        stats["userstories"] = services.get_user_stories_stats()
        return response.Ok(stats)

    def _get_cache_timeout(self):
        return getattr(settings, "STATS_CACHE_TIMEOUT", 0)

    def dispatch(self, *args, **kwargs):
        return cache_page(self._get_cache_timeout())(super().dispatch)(*args, **kwargs)
