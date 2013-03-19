# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from .views import *

urlpatterns = patterns('',
    url(r'^$', SearchView.as_view(), name='search'),
)

