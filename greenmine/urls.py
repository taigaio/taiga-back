from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from greenmine.base.views import Login, Logout

urlpatterns = patterns('',
    url(r'^api/auth/login/$', Login.as_view(), name='api-login'),
    url(r'^api/auth/logout/$', Logout.as_view(), name='api-logout'),
    url(r'^api/$', 'greenmine.base.views.api_root'),
    url(r'^api/scrum/', include('greenmine.scrum.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

