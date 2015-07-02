# Copyright (C) 2015 Taiga Agile LLC <support@taiga.io>
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

from django.apps import AppConfig
from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url

from .routers import router


class StatsAppConfig(AppConfig):
    name = "taiga.stats"
    verbose_name = "Stats"

    def ready(self):
        if settings.STATS_ENABLED:
            from taiga.urls import urlpatterns
            urlpatterns.append(url(r'^api/v1/', include(router.urls)))
