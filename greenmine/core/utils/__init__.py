# -*- coding: utf-8 -*-

import unicodedata

class Singleton(type):
    """ Singleton metaclass. """
    def __init__(cls, name, bases, dct):
        cls.__instance = None
        type.__init__(cls, name, bases, dct)

    def __call__(cls, *args, **kw):
        if cls.__instance is None:
            cls.__instance = type.__call__(cls, *args,**kw)
        return cls.__instance


def iter_points(queryset):
    for item in queryset:
        if item.points == -1:
            yield 0
        elif item.points == -2:
            yield 0.5
        else:
            yield item.points


def clear_model_dict(data):
    hidden_fields = ['password']

    new_dict = {}
    for key, val in data.items():
        if not key.startswith('_') and key not in hidden_fields:
            new_dict[key] = val

    return new_dict


def normalize_tagname(tagname):
    value = unicodedata.normalize('NFKD', tagname).encode('ascii', 'ignore')
    return value.lower()
