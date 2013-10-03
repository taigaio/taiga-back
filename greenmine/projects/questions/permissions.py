# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class QuestionStatusPermission(BasePermission):
    get_permission = "view_questionstatus"
    put_permission = "change_questionstatus"
    patch_permission = "change_questionstatus"
    delete_permission = "delete_questionstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class QuestionPermission(BasePermission):
    get_permission = "can_view_question"
    put_permission = "change_question"
    patch_permission = "change_question"
    delete_permission = "delete_question"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]

