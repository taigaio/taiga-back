from functools import wraps, partial

def as_tuple(function=None, *, remove_nulls=False):
    if function is None:
        return partial(as_tuple, remove_nulls=remove_nulls)

    @wraps(function)
    def _decorator(*args, **kwargs):
        return list(function(*args, **kwargs))

    return _decorator


def as_dict(function):
    @wraps(function)
    def _decorator(*args, **kwargs):
        return dict(function(*args, **kwargs))
    return _decorator
