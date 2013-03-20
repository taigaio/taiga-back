from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from base.api_actions import Login, Logout

from tastypie.api import Api

from scrum.api import *
from questions.api import *
from documents.api import *
from profile.api import *
from taggit.api import *
from wiki.api import *

v1_api = Api(api_name='gm')
v1_api.register(ProjectResource())
v1_api.register(ProjectUserRoleResource())
v1_api.register(MilestoneResource())
v1_api.register(UserStoryResource())
v1_api.register(ChangeResource())
v1_api.register(ChangeAttachmentResource())
v1_api.register(TaskResource())
v1_api.register(QuestionResource())
v1_api.register(QuestionResponseResource())
v1_api.register(DocumentResource())
v1_api.register(ProfileResource())
v1_api.register(TagResource())
v1_api.register(TaggedItemResource())
v1_api.register(WikiPageResource())
v1_api.register(WikiPageHistoryResource())
v1_api.register(WikiPageAttachmentResource())

urlpatterns = patterns('',
    url(r'^api/gm/actions/login/', Login.as_view(), name="login"),
    url(r'^api/gm/actions/logout/', Logout.as_view(), name="logout"),
    url(r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

