from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'greenmine.views.home', name='home'),
    # url(r'^greenmine/', include('greenmine.foo.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
