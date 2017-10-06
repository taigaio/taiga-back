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
