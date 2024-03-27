# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _

from django_jinja import library


EXTRA_FIELD_VERBOSE_NAMES = {
    "description_diff": _("description"),
    "content_diff": _("content"),
    "blocked_note_diff": _("blocked note"),
    "milestone": _("sprint"),
}


@library.global_function
def verbose_name(obj_class, field_name):
    if field_name in EXTRA_FIELD_VERBOSE_NAMES:
        return EXTRA_FIELD_VERBOSE_NAMES[field_name]

    try:
        return obj_class._meta.get_field(field_name).verbose_name
    except Exception:
        return field_name


@library.global_function
def lists_diff(list1, list2):
    """
    Get the difference of two list and remove None values.

    >>> list1 = ["a", None, "b", "c"]
    >>> list2 = [None, "b", "d", "e"]
    >>> list(filter(None.__ne__, set(list1) - set(list2)))
    ['c', 'a']
    """
    return list(filter(None.__ne__, set(list1) - set(list2)))
