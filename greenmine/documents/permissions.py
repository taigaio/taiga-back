# -*- coding: utf-8 -*-

from greenmine.base.permissions import BaseDetailPermission


class DocumentPermission(BaseDetailPermission):
    get_permission = "can_view_document"
    put_permission = "can_change_document"
    delete_permission = "can_delete_document"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_document =  []
