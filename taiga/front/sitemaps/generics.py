# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.apps import apps

from taiga.front.templatetags.functions import resolve

from .base import Sitemap


class GenericSitemap(Sitemap):
    def items(self):
        return [
            {"url_key": "home", "changefreq": "monthly", "priority": 1},
            {"url_key": "discover", "changefreq": "daily", "priority": 1},
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

