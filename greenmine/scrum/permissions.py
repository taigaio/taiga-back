# -*- coding: utf-8 -*-

from greenmine.base.permissions import BaseDetailPermission


class ProjectDetailPermission(BaseDetailPermission):
    get_permission = "view_project"
    put_permission = "change_project"
    patch_permission = "change_project"
    delete_permission = "delete_project"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  []


class MilestoneDetailPermission(BaseDetailPermission):
    get_permission = "view_milestone"
    put_permission = "change_milestone"
    patch_permission = "change_milestone"
    delete_permission = "delete_milestone"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class UserStoryDetailPermission(BaseDetailPermission):
    get_permission = "view_userstory"
    put_permission = "change_userstory"
    patch_permission = "change_userstory"
    delete_permission = "delete_userstory"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class TaskDetailPermission(BaseDetailPermission):
    get_permission = "view_task"
    put_permission = "change_task"
    patch_permission = "change_task"
    delete_permission = "delete_task"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueDetailPermission(BaseDetailPermission):
    get_permission = "view_issue"
    put_permission = "change_issue"
    patch_permission = "change_issue"
    delete_permission = "delete_issue"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class AttachmentDetailPermission(BaseDetailPermission):
    get_permission = "view_attachment"
    put_permission = "change_attachment"
    patch_permission = "change_attachment"
    delete_permission = "delete_attachment"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class SeverityDetailPermission(BaseDetailPermission):
    get_permission = "view_severity"
    put_permission = "change_severity"
    patch_permission = "change_severity"
    delete_permission = "delete_severity"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueStatusDetailPermission(BaseDetailPermission):
    get_permission = "view_issuestatus"
    put_permission = "change_issuestatus"
    patch_permission = "change_issuestatus"
    delete_permission = "delete_issuestatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class TaskStatusDetailPermission(BaseDetailPermission):
    get_permission = "view_taskstatus"
    put_permission = "change_taskstatus"
    patch_permission = "change_taskstatus"
    delete_permission = "delete_taskstatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class UserStoryStatusDetailPermission(BaseDetailPermission):
    get_permission = "view_userstorystatus"
    put_permission = "change_userstorystatus"
    patch_permission = "change_userstorystatus"
    delete_permission = "delete_userstorystatus"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class PriorityDetailPermission(BaseDetailPermission):
    get_permission = "view_priority"
    put_permission = "change_priority"
    patch_permission = "change_priority"
    delete_permission = "delete_priority"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class IssueTypeDetailPermission(BaseDetailPermission):
    get_permission = "view_issuetype"
    put_permission = "severity_issuetype"
    patch_permission = "severity_issuetype"
    delete_permission = "delete_issuetype"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']


class PointsDetailPermission(BaseDetailPermission):
    get_permission = "view_points"
    put_permission = "severity_points"
    patch_permission = "severity_points"
    delete_permission = "delete_points"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  ['project']
