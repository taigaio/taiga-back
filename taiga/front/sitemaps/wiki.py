# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.apps import apps
from datetime import timedelta
from django.utils import timezone

from taiga.front.templatetags.functions import resolve

from .base import Sitemap


class WikiPagesSitemap(Sitemap):
    def items(self):
        wiki_page_model = apps.get_model("wiki", "WikiPage")

        # Get wiki pages of public projects OR private projects if anon user can view them
        queryset = wiki_page_model.objects.filter(Q(project__is_private=False) |
                                                  Q(project__is_private=True,
                                                    project__anon_permissions__contains=["view_wiki_pages"]))

        # Exclude blocked projects
        queryset = queryset.filter(project__blocked_code__isnull=True)

        # Exclude wiki pages from projects without wiki section enabled
        queryset = queryset.exclude(project__is_wiki_activated=False)

        # Project data is needed
        queryset = queryset.select_related("project")

        return queryset

    def location(self, obj):
        return resolve("wiki", obj.project.slug, obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=90):
            return "monthly"
        return "weekly"

    def priority(self, obj):
        return 0.6
