from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/auth/', include('rest_framework.urls',
        namespace='rest_framework')),
    url(r'^api/$', 'greenmine.base.views.api_root'),
    url(r'^api/scrum/', include('greenmine.scrum.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

