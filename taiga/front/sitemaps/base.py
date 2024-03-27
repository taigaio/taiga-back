# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings
from django.contrib.sitemaps import Sitemap as DjangoSitemap


class Sitemap(DjangoSitemap):
    limit = settings.FRONT_SITEMAP_PAGE_SIZE

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []
        latest_lastmod = None
        all_items_lastmod = True  # track if all items have a lastmod
        for item in self.paginator.page(page).object_list:
            loc = self._get('location', item)
            priority = self._get('priority', item, None)
            lastmod = self._get('lastmod', item, None)
            changefreq = self._get('changefreq', item, None)
            if all_items_lastmod:
                all_items_lastmod = lastmod is not None
                if (all_items_lastmod and
                        (latest_lastmod is None or lastmod > latest_lastmod)):
                    latest_lastmod = lastmod
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': lastmod,
                'changefreq': changefreq,
                'priority': str(priority if priority is not None else ''),
            }
            urls.append(url_info)
        if all_items_lastmod and latest_lastmod:
            self.latest_lastmod = latest_lastmod

        return urls
