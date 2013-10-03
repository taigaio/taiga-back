# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

from .routers import router


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/v1/', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()
