from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from tastypie.api import Api

from scrum.api import *

v1_api = Api(api_name='v1')
v1_api.register(ProjectResource())
v1_api.register(ProjectUserRoleResource())
v1_api.register(MilestoneResource())
v1_api.register(UserStoryResource())
v1_api.register(ChangeResource())
v1_api.register(ChangeAttachmentResource())
v1_api.register(TaskResource())

urlpatterns = patterns('',
    url(r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

