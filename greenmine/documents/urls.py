# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from . import api


urlpatterns = format_suffix_patterns(patterns('',
    url(r'^documents/$', api.DocumentList.as_view(), name='document-list'),
    url(r'^documents/(?P<pk>[0-9]+)/$', api.DocumentDetail.as_view(), name='document-detail'),
))

