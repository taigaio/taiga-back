# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class MilestonePermission(BasePermission):
    get_permission = "view_milestone"
    post_permission = "add_milestone"
    put_permission = "change_milestone"
    patch_permission = "change_milestone"
    delete_permission = "delete_milestone"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]

