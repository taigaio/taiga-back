# -*- coding: utf-8 -*-

import functools

def as_list(function):
    """
    Convert to list a generator function.
    """
    @functools.wraps(function)
    def _decorator(*args, **kwargs):
        return list(function(*args, **kwargs))

    return _decorator
