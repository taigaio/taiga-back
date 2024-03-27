# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from functools import wraps, partial
from django.core.paginator import Paginator


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


def split_by_n(seq:str, n:int):
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]


def iter_queryset(queryset, itersize:int=20):
    """
    Util function for iterate in more efficient way
    all queryset.
    """
    paginator = Paginator(queryset, itersize)
    for page_num in paginator.page_range:
        page = paginator.page(page_num)
        for element in page.object_list:
            yield element
