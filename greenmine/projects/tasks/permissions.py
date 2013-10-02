# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class TaskPermission(BasePermission):
    get_permission = "view_task"
    put_permission = "change_task"
    patch_permission = "change_task"
    delete_permission = "delete_task"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class TaskStatusPermission(BasePermission):
    get_permission = "view_taskstatus"
    put_permission = "change_taskstatus"
    patch_permission = "change_taskstatus"
    delete_permission = "delete_taskstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
