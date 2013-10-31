# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class TaskPermission(BasePermission):
    get_permission = "view_task"
    post_permission = "add_task"
    put_permission = "change_task"
    patch_permission = "change_task"
    delete_permission = "delete_task"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
