# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from . import api


urlpatterns = format_suffix_patterns(patterns('',
    url(r'^questions/$', api.QuestionList.as_view(), name='question-list'),
    url(r'^questions/(?P<pk>[0-9]+)/$', api.QuestionDetail.as_view(), name='question-detail'),
))

