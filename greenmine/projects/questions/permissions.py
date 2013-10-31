# -*- coding: utf-8 -*-

from greenmine.base.permissions import BasePermission


class QuestionPermission(BasePermission):
    get_permission = "view_question"
    post_permission = "add_question"
    put_permission = "change_question"
    patch_permission = "change_question"
    delete_permission = "delete_question"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]

