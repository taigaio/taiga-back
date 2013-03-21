# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

from greenmine.search.views import SearchView

urlpatterns = patterns('',
    url(r'^$', SearchView.as_view(), name='search'),
)
