# -*- coding: utf-8 -*-
from functools import wraps

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

