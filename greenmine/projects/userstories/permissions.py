# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class UserStoryPermission(BasePermission):
    get_permission = "view_userstory"
    post_permission = "add_userstory"
    put_permission = "change_userstory"
    patch_permission = "change_userstory"
    delete_permission = "delete_userstory"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
