# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.sitemaps import Sitemap as DjangoSitemap


class Sitemap(DjangoSitemap):
    limit = settings.FRONT_SITEMAP_PAGE_SIZE

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []
        latest_lastmod = None
        all_items_lastmod = True  # track if all items have a lastmod
        for item in self.paginator.page(page).object_list:
            loc = self.__get('location', item)
            priority = self.__get('priority', item, None)
            lastmod = self.__get('lastmod', item, None)
            if all_items_lastmod:
                all_items_lastmod = lastmod is not None
                if (all_items_lastmod and
                        (latest_lastmod is None or lastmod > latest_lastmod)):
                    latest_lastmod = lastmod
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': lastmod,
                'changefreq': self.__get('changefreq', item, None),
                'priority': str(priority if priority is not None else ''),
            }
            urls.append(url_info)
        if all_items_lastmod and latest_lastmod:
            self.latest_lastmod = latest_lastmod

        return urls
