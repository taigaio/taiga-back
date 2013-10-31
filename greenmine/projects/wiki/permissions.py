# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class WikiPagePermission(BasePermission):
    get_permission = "view_wikipage"
    post_permission = "add_wikipage"
    put_permission = "change_wikipage"
    patch_permission = "change_wikipage"
    delete_permission = "delete_wikipage"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
