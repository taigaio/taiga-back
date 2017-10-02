# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps
from django.contrib.auth import get_user_model

from taiga.front.templatetags.functions import resolve

from .base import Sitemap


class UsersSitemap(Sitemap):
    def items(self):
        user_model = get_user_model()

        # Only active users and not system users
        queryset = user_model.objects.filter(is_active=True,
                                             is_system=False)

        return queryset

    def location(self, obj):
        return resolve("user", obj.username)

    def lastmod(self, obj):
        return None

    def changefreq(self, obj):
        return "weekly"

    def priority(self, obj):
        return 0.5
