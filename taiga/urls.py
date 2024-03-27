# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings
from django.urls import include, re_path
from django.contrib import admin
from django.urls import path

from .routers import router


##############################################
# Default
##############################################

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('admin/', admin.site.urls),
]

handler500 = "taiga.base.api.views.api_server_error"


##############################################
# Front sitemap
##############################################

if settings.FRONT_SITEMAP_ENABLED:
    from django.contrib.sitemaps.views import index
    from django.contrib.sitemaps.views import sitemap
    from django.views.decorators.cache import cache_page

    from taiga.front.sitemaps import sitemaps

    urlpatterns += [
        re_path(r"^front/sitemap\.xml$",
            cache_page(settings.FRONT_SITEMAP_CACHE_TIMEOUT)(index),
            {"sitemaps": sitemaps, 'sitemap_url_name': 'front-sitemap'},
            name="front-sitemap-index"),
        re_path(r"^front/sitemap-(?P<section>.+)\.xml$",
            cache_page(settings.FRONT_SITEMAP_CACHE_TIMEOUT)(sitemap),
            {"sitemaps": sitemaps},
            name="front-sitemap")
    ]


##############################################
# Static and media files in debug mode
##############################################

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    def mediafiles_urlpatterns(prefix):
        """
        Method for serve media files with runserver.
        """
        import re
        from django.views.static import serve

        return [
            re_path(r'^%s(?P<path>.*)$' % re.escape(prefix.lstrip('/')), serve,
                {'document_root': settings.MEDIA_ROOT})
        ]

    # Hardcoded only for development server
    urlpatterns += staticfiles_urlpatterns(prefix="/static/")
    urlpatterns += mediafiles_urlpatterns(prefix="/media/")
