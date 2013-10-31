# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class IssuePermission(BasePermission):
    get_permission = "view_issue"
    post_permission = "add_issue"
    put_permission = "change_issue"
    patch_permission = "change_issue"
    delete_permission = "delete_issue"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
