# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.apps import apps

from taiga.front.templatetags.functions import resolve
from datetime import timedelta
from django.utils import timezone

from .base import Sitemap


class ProjectsSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project"]))

        # Exclude blocked projects
        queryset = queryset.filter(blocked_code__isnull=True)
        queryset = queryset.exclude(description="")
        queryset = queryset.exclude(description__isnull=True)
        queryset = queryset.exclude(total_activity__gt=5)

        return queryset

    def location(self, obj):
        return resolve("project", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=30):
            return "monthly"
        return "daily"

    def priority(self, obj):
        return 0.8


class ProjectBacklogsSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them and user stories
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project",
                                                                              "view_us"]))

        queryset = queryset.exclude(description="")
        queryset = queryset.exclude(description__isnull=True)
        queryset = queryset.exclude(total_activity__gt=5)

        # Exclude projects without backlog enabled
        queryset = queryset.exclude(is_backlog_activated=False)

        return queryset

    def location(self, obj):
        return resolve("backlog", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=90):
            return "monthly"
        return "weekly"

    def priority(self, obj):
        return 0.1


class ProjectKanbansSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them and user stories
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project",
                                                                              "view_us"]))

        queryset = queryset.exclude(description="")
        queryset = queryset.exclude(description__isnull=True)
        queryset = queryset.exclude(total_activity__gt=5)

        # Exclude projects without kanban enabled
        queryset = queryset.exclude(is_kanban_activated=False)

        return queryset

    def location(self, obj):
        return resolve("kanban", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=90):
            return "monthly"
        return "weekly"

    def priority(self, obj):
        return 0.1
