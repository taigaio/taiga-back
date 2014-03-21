# -*- coding: utf-8 -*-
from functools import wraps
import warnings

def change_instance_attr(name, new_value):
    """
    Change the attribute value temporarily for a new one. If it raise an AttributeError (if the
    instance hasm't the attribute) the attribute will not be changed.
    """
    def change_instance_attr(fn):
        @wraps(fn)
        def wrapper(instance, *args, **kwargs):
            try:
                old_value = instance.__getattribute__(name)
                changed = True
            except AttributeError:
                changed = False

            if changed:
                instance.__setattr__(name, new_value)

            ret =  fn(instance, *args, **kwargs)

            if changed:
                instance.__setattr__(name, old_value)

            return ret
        return wrapper
    return change_instance_attr


## Rest Framework 2.4 backport some decorators.

def detail_route(methods=['get'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail requests.
    """
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = True
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
        func.kwargs = kwargs
        return func
    return decorator


def link(**kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail GET requests.
    """
    msg = 'link is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
    def decorator(func):
        func.bind_to_methods = ['get']
        func.detail = True
        func.kwargs = kwargs
        return func
    return decorator


def action(methods=['post'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail POST requests.
    """
    msg = 'action is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = True
        func.kwargs = kwargs
        return func
    return decorator
