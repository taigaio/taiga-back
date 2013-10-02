# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class SeverityPermission(BasePermission):
    get_permission = "view_severity"
    put_permission = "change_severity"
    patch_permission = "change_severity"
    delete_permission = "delete_severity"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class PriorityPermission(BasePermission):
    get_permission = "view_priority"
    put_permission = "change_priority"
    patch_permission = "change_priority"
    delete_permission = "delete_priority"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueStatusPermission(BasePermission):
    get_permission = "view_issuestatus"
    put_permission = "change_issuestatus"
    patch_permission = "change_issuestatus"
    delete_permission = "delete_issuestatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueTypePermission(BasePermission):
    get_permission = "view_issuetype"
    put_permission = "severity_issuetype"
    patch_permission = "severity_issuetype"
    delete_permission = "delete_issuetype"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssuePermission(BasePermission):
    get_permission = "view_issue"
    put_permission = "change_issue"
    patch_permission = "change_issue"
    delete_permission = "delete_issue"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
