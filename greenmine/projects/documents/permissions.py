# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class DocumentPermission(BasePermission):
    get_permission = "view_document"
    post_permission = "add_document"
    put_permission = "change_document"
    patch_permission = "change_document"
    delete_permission = "delete_document"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
