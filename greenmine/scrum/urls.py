# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from greenmine.scrum import api
from greenmine.base import routers


router = routers.DefaultRouter(trailing_slash=False)
router.register(r"projects", api.ProjectViewSet, base_name="projects")
router.register(r"milestones", api.MilestoneViewSet, base_name="milestones")
router.register(r"userstories", api.UserStoryViewSet, base_name="userstories")
router.register(r"issue-attachments", api.IssuesAttachmentViewSet, base_name="issue-attachments")
router.register(r"task-attachments", api.TasksAttachmentViewSet, base_name="task-attachments")
router.register(r"tasks", api.TaskViewSet, base_name="tasks")
router.register(r"issues", api.IssueViewSet, base_name="issues")
router.register(r"severities", api.SeverityViewSet, base_name="severities")
router.register(r"issue-statuses", api.IssueStatusViewSet, base_name="issue-statuses")
router.register(r"task-statuses", api.TaskStatusViewSet, base_name="task-statuses")
router.register(r"userstory-statuses", api.UserStoryStatusViewSet, base_name="userstory-statuses")
router.register(r"priorities", api.PriorityViewSet, base_name="priorities")
router.register(r"issue-types", api.IssueTypeViewSet, base_name="issue-types")
router.register(r"points", api.PointsViewSet, base_name="points")

urlpatterns = router.urls

#urlpatterns = format_suffix_patterns(patterns('',
#    url(r'^projects/$', api.ProjectList.as_view(), name='project-list'),
#    url(r'^projects/(?P<pk>[0-9]+)/$', api.ProjectDetail.as_view(), name='project-detail'),
#    url(r'^milestones/$', api.MilestoneList.as_view(), name='milestone-list'),
#    url(r'^milestones/(?P<pk>[0-9]+)/$', api.MilestoneDetail.as_view(), name='milestone-detail'),
#    url(r'^user-stories/$', api.UserStoryList.as_view(), name='user-story-list'),
#    url(r'^user-stories/(?P<pk>[0-9]+)/$', api.UserStoryDetail.as_view(), name='user-story-detail'),
#    url(r'^user-stories/points/$', api.PointsList.as_view(), name='points-list'),
#    url(r'^user-stories/points/(?P<pk>[0-9]+)/$', api.PointsDetail.as_view(), name='points-detail'),
#    url(r'^user-stories/statuses/$', api.UserStoryStatusList.as_view(), name='user-story-status-list'),
#    url(r'^user-stories/statuses/(?P<pk>[0-9]+)/$', api.UserStoryStatusDetail.as_view(), name='user-story-status-detail'),
#    url(r'^issues/$', api.IssueList.as_view(), name='issues-list'),
#    url(r'^issues/(?P<pk>[0-9]+)/$', api.IssueDetail.as_view(), name='issues-detail'),
#    url(r'^issues/attachments/$', api.IssuesAttachmentList.as_view(), name='issues-attachment-list'),
#    url(r'^issues/attachments/(?P<pk>[0-9]+)/$', api.IssuesAttachmentDetail.as_view(), name='issues-attachment-detail'),
#    url(r'^issues/statuses/$', api.IssueStatusList.as_view(), name='issues-status-list'),
#    url(r'^issues/statuses/(?P<pk>[0-9]+)/$', api.IssueStatusDetail.as_view(), name='issues-status-detail'),
#    url(r'^issues/types/$', api.IssueTypeList.as_view(), name='issues-type-list'),
#    url(r'^issues/types/(?P<pk>[0-9]+)/$', api.IssueTypeDetail.as_view(), name='issues-type-detail'),
#    url(r'^tasks/$', api.TaskList.as_view(), name='tasks-list'),
#    url(r'^tasks/(?P<pk>[0-9]+)/$', api.TaskDetail.as_view(), name='tasks-detail'),
#    url(r'^tasks/attachments/$', api.TasksAttachmentList.as_view(), name='tasks-attachment-list'),
#    url(r'^tasks/attachments/(?P<pk>[0-9]+)/$', api.TasksAttachmentDetail.as_view(), name='tasks-attachment-detail'),
#    url(r'^severities/$', api.SeverityList.as_view(), name='severity-list'),
#    url(r'^severities/(?P<pk>[0-9]+)/$', api.SeverityDetail.as_view(), name='severity-detail'),
#    url(r'^tasks/statuses/$', api.TaskStatusList.as_view(), name='tasks-status-list'),
#    url(r'^tasks/statuses/(?P<pk>[0-9]+)/$', api.TaskStatusDetail.as_view(), name='tasks-status-detail'),
#    url(r'^priorities/$', api.PriorityList.as_view(), name='priority-list'),
#    url(r'^priorities/(?P<pk>[0-9]+)/$', api.PriorityDetail.as_view(), name='priority-detail'),
#))
