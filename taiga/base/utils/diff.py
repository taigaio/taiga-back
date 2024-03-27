# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

def make_diff(first: dict, second: dict, not_found_value=None,
              excluded_keys: tuple = ()) -> dict:
    """
    Compute a diff between two dicts.
    """
    diff = {}
    # Check all keys in first dict
    for key in first:
        if key not in second:
            diff[key] = (first[key], not_found_value)
        elif first[key] != second[key]:
            diff[key] = (first[key], second[key])

    # Check all keys in second dict to find missing
    for key in second:
        if key not in first:
            diff[key] = (not_found_value, second[key])

    # Remove A -> A changes that usually happens with None -> None
    for key, value in list(diff.items()):
        frst, scnd = value
        if frst == scnd:
            del diff[key]

    # Removed excluded keys
    for key in excluded_keys:
        if key in diff:
            del diff[key]

    return diff
