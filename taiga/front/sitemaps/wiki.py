# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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


class WikiPagesSitemap(Sitemap):
    def items(self):
        wiki_page_model = apps.get_model("wiki", "WikiPage")

        # Get wiki pages of public projects OR private projects if anon user can view them
        queryset = wiki_page_model.objects.filter(Q(project__is_private=False) |
                                                  Q(project__is_private=True,
                                                    project__anon_permissions__contains=["view_wiki_pages"]))

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
        return "daily"

    def priority(self, obj):
        return 0.6
