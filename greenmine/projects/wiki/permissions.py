# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class WikiPagePermission(BasePermission):
    get_permission = "can_view_wikipage"
    put_permission = "change_wikipage"
    patch_permission = "change_wikipage"
    delete_permission = "can_delete_wikipage"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class WikiPageAttachmentPermission(BasePermission):
    get_permission = "can_view_wikipageattachment"
    put_permission = "change_wikipageattachment"
    patch_permission = "change_wikipageattachment"
    delete_permission = "can_delete_wikipageattachment"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
