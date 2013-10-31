# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class ProjectPermission(BasePermission):
    get_permission = "view_project"
    post_permission = "add_project"
    put_permission = "change_project"
    patch_permission = "change_project"
    delete_permission = "delete_project"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  []


class MembershipPermission(BasePermission):
    get_permission = "view_membership"
    post_permission = "add_membership"
    put_permission = "change_membership"
    patch_permission = "change_membership"
    delete_permission = "delete_membership"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class AttachmentPermission(BasePermission):
    get_permission = "view_attachment"
    post_permission = "add_attachment"
    put_permission = "change_attachment"
    patch_permission = "change_attachment"
    delete_permission = "delete_attachment"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# User Stories

class PointsPermission(BasePermission):
    get_permission = "view_points"
    post_permission = "add_points"
    put_permission = "change_points"
    patch_permission = "change_points"
    delete_permission = "delete_points"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class UserStoryStatusPermission(BasePermission):
    get_permission = "view_userstorystatus"
    post_permission = "add_userstorystatus"
    put_permission = "change_userstorystatus"
    patch_permission = "change_userstorystatus"
    delete_permission = "delete_userstorystatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Tasks

class TaskStatusPermission(BasePermission):
    get_permission = "view_taskstatus"
    post_permission = "ade_taskstatus"
    put_permission = "change_taskstatus"
    patch_permission = "change_taskstatus"
    delete_permission = "delete_taskstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Issues

class SeverityPermission(BasePermission):
    get_permission = "view_severity"
    post_permission = "add_severity"
    put_permission = "change_severity"
    patch_permission = "change_severity"
    delete_permission = "delete_severity"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class PriorityPermission(BasePermission):
    get_permission = "view_priority"
    post_permission = "add_priority"
    put_permission = "change_priority"
    patch_permission = "change_priority"
    delete_permission = "delete_priority"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueStatusPermission(BasePermission):
    get_permission = "view_issuestatus"
    post_permission = "add_issuestatus"
    put_permission = "change_issuestatus"
    patch_permission = "change_issuestatus"
    delete_permission = "delete_issuestatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueTypePermission(BasePermission):
    get_permission = "view_issuetype"
    post_permission = "add_issuetype"
    put_permission = "change_issuetype"
    patch_permission = "change_issuetype"
    delete_permission = "delete_issuetype"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Questions

class QuestionStatusPermission(BasePermission):
    get_permission = "view_questionstatus"
    post_permission = "add_questionstatus"
    put_permission = "change_questionstatus"
    patch_permission = "change_questionstatus"
    delete_permission = "delete_questionstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
