# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Taiga Agile LLC <support@taiga.io>
#
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

from django.db.models import Q
from django.apps import apps

from taiga.front.templatetags.functions import resolve

from .base import Sitemap


class GenericSitemap(Sitemap):
    def items(self):
        return [
            {"url_key": "home", "changefreq": "monthly", "priority": 1},
            {"url_key": "login", "changefreq": "monthly", "priority": 1},
            {"url_key": "register", "changefreq": "monthly", "priority": 1},
            {"url_key": "forgot-password", "changefreq": "monthly", "priority": 1}
        ]

    def location(self, obj):
        return resolve(obj["url_key"])

    def changefreq(self, obj):
        return obj.get("changefreq", None)

    def priority(self, obj):
        return obj.get("priority", None)

