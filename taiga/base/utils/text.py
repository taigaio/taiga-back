# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

def strip_lines(text):
    """
    Given text, try remove unnecessary spaces and
    put text in one unique line.
    """
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").strip()


def split_in_lines(text):
    """Split a block of text in lines removing unnecessary spaces from each line."""
    return (line for line in map(str.strip, text.split("\n")) if line)
