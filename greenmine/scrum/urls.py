from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from greenmine.scrum import api

urlpatterns = format_suffix_patterns(patterns('',
    url(r'^projects/$', api.ProjectList.as_view(), name='project-list'),
    url(r'^projects/(?P<pk>[0-9]+)/$', api.ProjectDetail.as_view(), name='project-detail'),
    url(r'^milestones/$', api.MilestoneList.as_view(), name='milestone-list'),
    url(r'^milestones/(?P<pk>[0-9]+)/$', api.MilestoneDetail.as_view(), name='milestone-detail'),
    url(r'^user_stories/$', api.UserStoryList.as_view(), name='user-story-list'),
    url(r'^user_stories/(?P<pk>[0-9]+)/$', api.UserStoryDetail.as_view(), name='user-story-detail'),
    url(r'^changes/$', api.ChangeList.as_view(), name='change-list'),
    url(r'^changes/(?P<pk>[0-9]+)/$', api.ChangeDetail.as_view(), name='change-detail'),
    url(r'^change_attachments/$', api.ChangeAttachmentList.as_view(), name='change-attachment-list'),
    url(r'^change_attachments/(?P<pk>[0-9]+)/$', api.ChangeAttachmentDetail.as_view(), name='change-attachment-detail'),
    url(r'^tasks/$', api.TaskList.as_view(), name='task-list'),
    url(r'^tasks/(?P<pk>[0-9]+)/$', api.TaskDetail.as_view(), name='task-detail'),
    url(r'^issues/$', api.IssueList.as_view(), name='issue-list'),
    url(r'^issues/(?P<pk>[0-9]+)/$', api.IssueDetail.as_view(), name='issue-detail'),
    url(r'^severities/$', api.SeverityList.as_view(), name='severity-list'),
    url(r'^severities/(?P<pk>[0-9]+)/$', api.SeverityDetail.as_view(), name='severity-detail'),
    url(r'^issue_status/$', api.IssueStatusList.as_view(), name='issue-status-list'),
    url(r'^issue_status/(?P<pk>[0-9]+)/$', api.IssueStatusDetail.as_view(), name='issue-status-detail'),
    url(r'^task_status/$', api.TaskStatusList.as_view(), name='task-status-list'),
    url(r'^task_status/(?P<pk>[0-9]+)/$', api.TaskStatusDetail.as_view(), name='task-status-detail'),
    url(r'^user_story_status/$', api.UserStoryStatusList.as_view(), name='user-story-status-list'),
    url(r'^user_story_status/(?P<pk>[0-9]+)/$', api.UserStoryStatusDetail.as_view(), name='user-story-status-detail'),
    url(r'^priorities/$', api.PriorityList.as_view(), name='priority-list'),
    url(r'^priorities/(?P<pk>[0-9]+)/$', api.PriorityDetail.as_view(), name='priority-detail'),
    url(r'^issue_types/$', api.IssueTypeList.as_view(), name='issue-type-list'),
    url(r'^issue_types/(?P<pk>[0-9]+)/$', api.IssueTypeDetail.as_view(), name='issue-type-detail'),
    url(r'^points/$', api.PointsList.as_view(), name='points-list'),
    url(r'^points/(?P<pk>[0-9]+)/$', api.PointsDetail.as_view(), name='points-detail'),
))

