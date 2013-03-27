from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from greenmine.base.views import Login, Logout, ApiRoot

urlpatterns = format_suffix_patterns(patterns('',
    url(r'^auth/login/$', Login.as_view(), name='login'),
    url(r'^auth/logout/$', Logout.as_view(), name='logout'),
    url(r'^$', ApiRoot.as_view(), name='api_root'),
))
