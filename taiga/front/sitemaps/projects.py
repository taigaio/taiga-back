# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Taiga Agile LLC <support@taiga.io>
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


class ProjectsSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project"]))

        return queryset

    def location(self, obj):
        return resolve("project", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "hourly"

    def priority(self, obj):
        return 0.9


class ProjectBacklogsSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them and user stories
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project",
                                                                              "view_us"]))

        # Exclude projects without backlog enabled
        queryset = queryset.exclude(is_backlog_activated=False)

        return queryset

    def location(self, obj):
        return resolve("backlog", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.6


class ProjectKanbansSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them and user stories
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project",
                                                                              "view_us"]))

        # Exclude projects without kanban enabled
        queryset = queryset.exclude(is_kanban_activated=False)

        return queryset

    def location(self, obj):
        return resolve("kanban", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.6


class ProjectIssuesSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them and issues
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project",
                                                                              "view_issues"]))

        # Exclude projects without issues enabled
        queryset = queryset.exclude(is_issues_activated=False)

        return queryset

    def location(self, obj):
        return resolve("issues", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.6


class ProjectTeamsSitemap(Sitemap):
    def items(self):
        project_model = apps.get_model("projects", "Project")

        # Get public projects OR private projects if anon user can view them
        queryset = project_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_project"]))

        return queryset

    def location(self, obj):
        return resolve("team", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.6
