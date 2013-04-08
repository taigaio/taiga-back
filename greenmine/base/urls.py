# -*- coding: utf-8 -*-

from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls import patterns, url
from greenmine.base import api


urlpatterns = format_suffix_patterns(patterns('',
    url(r'^auth/login/$', api.Login.as_view(), name='login'),
    url(r'^auth/logout/$', api.Logout.as_view(), name='logout'),
    url(r'^users/$', api.UserList.as_view(), name="user-list"),
    url(r'^$', api.ApiRoot.as_view(), name='api_root'),
))
