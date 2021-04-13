# -*- coding: utf-8 -*-
from django_pglocks import advisory_lock


def detail_route(methods=['get'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail requests.
    """
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = True
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func
    return decorator


def list_route(methods=['get'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for list requests.
    """
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = False
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func
    return decorator


def model_pk_lock(func):
    """
    This decorator is designed to be used in ModelViewsets methods to lock them based
    on the model and the id of the selected object.
    """
    def decorator(self, *args, **kwargs):
        from taiga.base.utils.db import get_typename_for_model_class
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        tn = get_typename_for_model_class(self.get_queryset().model)
        key = "{0}:{1}".format(tn, pk)

        with advisory_lock(key):
            return func(self, *args, **kwargs)

    return decorator
