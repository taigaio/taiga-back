# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import collections


def dict_sum(*args):
    result = collections.Counter()
    for arg in args:
        assert isinstance(arg, dict)
        result += collections.Counter(arg)
    return result


def into_namedtuple(dictionary):
    return collections.namedtuple('GenericDict', dictionary.keys())(**dictionary)
