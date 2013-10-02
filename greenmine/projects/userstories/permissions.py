# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class PointsDetailPermission(BasePermission):
    get_permission = "view_points"
    put_permission = "severity_points"
    patch_permission = "severity_points"
    delete_permission = "delete_points"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class UserStoryStatusDetailPermission(BasePermission):
    get_permission = "view_userstorystatus"
    put_permission = "change_userstorystatus"
    patch_permission = "change_userstorystatus"
    delete_permission = "delete_userstorystatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class UserStoryPermission(BasePermission):
    get_permission = "view_userstory"
    put_permission = "change_userstory"
    patch_permission = "change_userstory"
    delete_permission = "delete_userstory"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
