# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class ProjectPermission(BasePermission):
    get_permission = "view_project"
    put_permission = "change_project"
    patch_permission = "change_project"
    delete_permission = "delete_project"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  []


class AttachmentPermission(BasePermission):
    get_permission = "view_attachment"
    put_permission = "change_attachment"
    patch_permission = "change_attachment"
    delete_permission = "delete_attachment"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
