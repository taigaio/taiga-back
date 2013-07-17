# -*- coding: utf-8 -*-

from greenmine.base.permissions import BaseDetailPermission


class ProjectDetailPermission(BaseDetailPermission):
    get_permission = "can_view_project"
    put_permission = "can_change_project"
    patch_permission = "can_change_project"
    delete_permission = "can_delete_project"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  []


class MilestoneDetailPermission(BaseDetailPermission):
    get_permission = "can_view_milestone"
    put_permission = "can_change_milestone"
    patch_permission = "can_change_milestone"
    delete_permission = "can_delete_milestone"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class UserStoryDetailPermission(BaseDetailPermission):
    get_permission = "can_view_userstory"
    put_permission = "can_change_userstory"
    patch_permission = "can_change_userstory"
    delete_permission = "can_delete_userstory"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class TaskDetailPermission(BaseDetailPermission):
    get_permission = "can_view_task"
    put_permission = "can_change_task"
    patch_permission = "can_change_task"
    delete_permission = "can_delete_task"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueDetailPermission(BaseDetailPermission):
    get_permission = "can_view_issue"
    put_permission = "can_change_issue"
    patch_permission = "can_change_issue"
    delete_permission = "can_delete_issue"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class AttachmentDetailPermission(BaseDetailPermission):
    get_permission = "can_view_attachment"
    put_permission = "can_change_attachment"
    patch_permission = "can_change_attachment"
    delete_permission = "can_delete_attachment"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['change', 'project']


class SeverityDetailPermission(BaseDetailPermission):
    get_permission = "can_view_severity"
    put_permission = "can_change_severity"
    patch_permission = "can_change_severity"
    delete_permission = "can_delete_severity"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueStatusDetailPermission(BaseDetailPermission):
    get_permission = "can_view_issuestatus"
    put_permission = "can_change_issuestatus"
    patch_permission = "can_change_issuestatus"
    delete_permission = "can_delete_issuestatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class TaskStatusDetailPermission(BaseDetailPermission):
    get_permission = "can_view_taskstatus"
    put_permission = "can_change_taskstatus"
    patch_permission = "can_change_taskstatus"
    delete_permission = "can_delete_taskstatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class UserStoryStatusDetailPermission(BaseDetailPermission):
    get_permission = "can_view_userstorystatus"
    put_permission = "can_change_userstorystatus"
    patch_permission = "can_change_userstorystatus"
    delete_permission = "can_delete_userstorystatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class PriorityDetailPermission(BaseDetailPermission):
    get_permission = "can_view_priority"
    put_permission = "can_change_priority"
    patch_permission = "can_change_priority"
    delete_permission = "can_delete_priority"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueTypeDetailPermission(BaseDetailPermission):
    get_permission = "can_view_issuetype"
    put_permission = "can_severity_issuetype"
    patch_permission = "can_severity_issuetype"
    delete_permission = "can_delete_issuetype"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class PointsDetailPermission(BaseDetailPermission):
    get_permission = "can_view_points"
    put_permission = "can_severity_points"
    patch_permission = "can_severity_points"
    delete_permission = "can_delete_points"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']
