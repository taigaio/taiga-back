# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

from greenmine.base import routers
from greenmine.base.api import ApiRoot
from greenmine.base.users.api import (
    LoginViewSet,
    LogoutViewSet,
    RolesViewSet,
    UsersViewSet
)
from greenmine.base.searches.api import SearchViewSet
from greenmine.scrum.api import (
    MilestoneViewSet,
    PriorityViewSet,
    ProjectViewSet,
    SeverityViewSet,
    UserStoryStatusViewSet,
    UserStoryViewSet,
    TaskStatusViewSet,
    TaskViewSet,
    TasksAttachmentViewSet,
    PointsViewSet,
    IssueStatusViewSet,
    IssueTypeViewSet,
    IssueViewSet,
    IssuesAttachmentViewSet
)


router = routers.DefaultRouter(trailing_slash=False)
# greenmine.base.users
router.register(r"users", UsersViewSet, base_name="users")
router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"auth/login", LoginViewSet, base_name="auth-login")
router.register(r"auth/logout", LogoutViewSet, base_name="auth-logout")
# greenmine.base.searches
router.register(r"search", SearchViewSet, base_name="search")
# greenmine.scrum
router.register(r"projects", ProjectViewSet, base_name="projects")
router.register(r"milestones", MilestoneViewSet, base_name="milestones")
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"issue-attachments", IssuesAttachmentViewSet, base_name="issue-attachments")
router.register(r"task-attachments", TasksAttachmentViewSet, base_name="task-attachments")
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"severities", SeverityViewSet, base_name="severities")
router.register(r"issue-statuses", IssueStatusViewSet, base_name="issue-statuses")
router.register(r"task-statuses", TaskStatusViewSet, base_name="task-statuses")
router.register(r"userstory-statuses", UserStoryStatusViewSet, base_name="userstory-statuses")
router.register(r"priorities", PriorityViewSet, base_name="priorities")
router.register(r"issue-types", IssueTypeViewSet, base_name="issue-types")
router.register(r"points", PointsViewSet, base_name="points")
#greenmine.issues
#greenmine.wiki
#greenmine.documents

urlpatterns = patterns('',
    url(r'^api/v1$', ApiRoot.as_view()),
    url(r'^api/v1/', include(router.urls)),
    # TODO: Refactor to use ViewSet
    #url(r'^api/v1/', include('greenmine.wiki.urls')),
    # TODO: Finish the documents and questions app
    #url(r'^api/v1/', include('greenmine.questions.urls')),
    #url(r'^api/v1/', include('greenmine.documents.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()
