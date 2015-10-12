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


class IssuesSitemap(Sitemap):
    def items(self):
        issue_model = apps.get_model("issues", "Issue")

        # Get issues of public projects OR private projects if anon user can view them
        queryset = issue_model.objects.filter(Q(project__is_private=False) |
                                              Q(project__is_private=True,
                                                project__anon_permissions__contains=["view_issues"]))

        # Project data is needed
        queryset = queryset.select_related("project")

        return queryset

    def location(self, obj):
        return resolve("issue", obj.project.slug, obj.ref)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.6
