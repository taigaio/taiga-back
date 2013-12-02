# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

from .routers import router


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/sites', "greenmine.base.apiviews.sitestatus"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)


def mediafiles_urlpatterns():
    """
    Method for serve media files with runserver.
    """

    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]

    from django.views.static import serve
    return patterns('',
        (r'^%s(?P<path>.*)$' % 'media', serve,
            {'document_root': settings.MEDIA_ROOT})
    )


urlpatterns += staticfiles_urlpatterns()
urlpatterns += mediafiles_urlpatterns()
