# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from greenmine.wiki import api


urlpatterns = format_suffix_patterns(patterns('',
    url(r'^pages/$', api.WikiPageList.as_view(), name='wiki-page-list'),
    url(r'^pages/(?P<projectid>\d+)-(?P<slug>[\w\-\d]+)/$', api.WikiPageDetail.as_view(), name='wiki-page-detail'),
    #url(r'^wiki_page_attachments/$', api.WikiPageAttachmentList.as_view(), name='wiki-page-attachment-list'),
    #url(r'^wiki_page_attachments/(?P<pk>[0-9]+)/$', api.WikiPageAttachmentDetail.as_view(), name='wiki-page-attachment-detail'),
))

