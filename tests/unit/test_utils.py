# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import pytest

from unittest import mock

import django_sites as sites
import re

from taiga.base.utils.urls import get_absolute_url, is_absolute_url, build_url
from taiga.base.utils.db import save_in_bulk, update_in_bulk, to_tsquery

pytestmark = pytest.mark.django_db


def test_is_absolute_url():
    assert is_absolute_url("http://domain/path")
    assert is_absolute_url("https://domain/path")
    assert not is_absolute_url("://domain/path")


def test_get_absolute_url():
    site = sites.get_current()
    assert get_absolute_url("http://domain/path") == "http://domain/path"
    assert get_absolute_url("/path") == build_url("/path", domain=site.domain, scheme=site.scheme)


def test_save_in_bulk():
    instance = mock.Mock()
    instances = [instance, instance]

    save_in_bulk(instances)

    assert instance.save.call_count == 2


def test_save_in_bulk_with_a_callback():
    instance = mock.Mock()
    callback = mock.Mock()
    instances = [instance, instance]

    save_in_bulk(instances, callback)

    assert callback.call_count == 2


def test_update_in_bulk():
    instance = mock.Mock()
    instances = [instance, instance]
    new_values = [{"field1": 1}, {"field2": 2}]

    update_in_bulk(instances, new_values)

    assert instance.save.call_count == 2
    assert instance.field1 == 1
    assert instance.field2 == 2


def test_update_in_bulk_with_a_callback():
    instance = mock.Mock()
    callback = mock.Mock()
    instances = [instance, instance]
    new_values = [{"field1": 1}, {"field2": 2}]

    update_in_bulk(instances, new_values, callback)

    assert callback.call_count == 2


TS_QUERY_TRANSFORMATIONS = [
    ("1 OR 2", "1 | 2"),
    ("(1) 2", "( 1 ) & 2"),
    ("&", "'&':*"),
    ('"hello world"', "'hello world'"),
    ("not 1", "! 1"),
    ("1 and not (2 or 3)", "1 & ! ( 2 | 3 )"),
    ("not and and 1) or ( 2 not", "! 1 | ( 2 )"),
    ("() 1", "1"),
    ("1 2 3", "1 & 2 & 3"),
    ("'&' |", "'&':* & '|':*"),
    (") and 1 (2 or", "1 & ( 2 )"),
    ("it's '", "'its':*"),
    ("(1)", "( 1 )"),
    ("1((", "1"),
    ("test\\", "'test':*"),
    ('"', "'\"':*"),
    ('""', "'\"\"':*"),
    ('"""', "'\"\"':* & '\"':*"),
]
def test_to_tsquery():
    for (input, expected) in TS_QUERY_TRANSFORMATIONS:
        expected = re.sub("([0-9])", r"'\1':*", expected)
        actual = to_tsquery(input)
        assert actual == expected
