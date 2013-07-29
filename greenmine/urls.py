# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

from greenmine.base.api import ApiRoot


urlpatterns = patterns('',
    url(r'^api/v1/core/', include('greenmine.base.urls')),
    url(r'^api/v1/scrum/', include('greenmine.scrum.urls')),
    url(r'^api/v1/documents/', include('greenmine.documents.urls')),
    url(r'^api/v1/questions/', include('greenmine.questions.urls')),
    url(r'^api/v1/wiki/', include('greenmine.wiki.urls')),
    url(r'^api/v1$', ApiRoot.as_view()),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()
