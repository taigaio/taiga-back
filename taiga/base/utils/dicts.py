# -*- coding: utf-8 -*-
import collections


def dict_sum(*args):
    result = collections.Counter()
    for arg in args:
        assert isinstance(arg, dict)
        result += collections.Counter(arg)
    return result


def into_namedtuple(dictionary):
    return collections.namedtuple('GenericDict', dictionary.keys())(**dictionary)
