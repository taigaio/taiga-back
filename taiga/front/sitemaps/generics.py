# -*- coding: utf-8 -*-
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

