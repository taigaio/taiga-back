# -*- coding: utf-8 -*-

from greenmine.base.permissions import BaseDetailPermission


class QuestionDetailPermission(BaseDetailPermission):
    get_permission = "can_view_question"
    put_permission = "change_question"
    patch_permission = "change_question"
    delete_permission = "delete_question"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  []

