# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

from greenmine.base.api import ApiRoot


urlpatterns = patterns('',
    url(r'^api/v1/', include('greenmine.base.urls')),
    url(r'^api/v1/', include('greenmine.scrum.urls')),
    url(r'^api/v1/', include('greenmine.wiki.urls')),
    # TODO: Finish the documents and questions app
    #url(r'^api/v1/', include('greenmine.questions.urls')),
    #url(r'^api/v1/', include('greenmine.documents.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()
