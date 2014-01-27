import collections


def dict_sum(*args):
    result = collections.Counter()
    for arg in args:
        assert isinstance(arg, dict)
        result += collections.Counter(arg)
    return result
