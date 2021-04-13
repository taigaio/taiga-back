# -*- coding: utf-8 -*-
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
