# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/core/', include('greenmine.base.urls')),
    url(r'^api/scrum/', include('greenmine.scrum.urls')),
    url(r'^api/documents/', include('greenmine.documents.urls')),
    url(r'^api/questions/', include('greenmine.questions.urls')),
    url(r'^api/wiki/', include('greenmine.wiki.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()
