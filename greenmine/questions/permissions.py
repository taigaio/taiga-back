from greenmine.base.permissions import BaseDetailPermission

class QuestionDetailPermission(BaseDetailPermission):
    get_permission = "can_view_question"
    put_permission = "can_change_question"
    delete_permission = "can_delete_question"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_document =  []

class QuestionResponseDetailPermission(BaseDetailPermission):
    get_permission = "can_view_questionresponse"
    put_permission = "can_change_questionresponse"
    delete_permission = "can_delete_questionresponse"
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_document =  []
