from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from greenmine.base.views import ApiRoot

urlpatterns = patterns('',
    url(r'^api/', include('greenmine.base.urls')),
    url(r'^api/scrum/', include('greenmine.scrum.urls')),
    url(r'^api/documents/', include('greenmine.documents.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

