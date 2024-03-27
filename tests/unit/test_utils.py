# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from unittest import mock

import django_sites as sites
import re

from taiga.base.utils.urls import get_absolute_url, is_absolute_url, build_url, \
    validate_private_url, IpAddresValueError, HostnameException
from taiga.base.utils.db import save_in_bulk, update_in_bulk, to_tsquery

pytestmark = pytest.mark.django_db(transaction=True)


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


@pytest.mark.parametrize("url", [
    "http://127.0.0.1",
    "http://[::1]",
    "http://192.168.0.12",
    "http://10.0.0.1",
    "https://172.25.0.1",
    "https://10.25.23.100",
    "ftp://192.168.1.100/",
    "http://[::ffff:c0a8:164]/",
    "scp://192.168.1.100/",
    "http://www.192-168-1-100.sslip.io/",
])
def test_validate_bad_destination_address(url):
    with pytest.raises(IpAddresValueError):
        validate_private_url(url)


@pytest.mark.parametrize("url", [
    "http://test.local/",
    "http://test.test/",
])
def test_validate_invalid_destination_address(url):
    with pytest.raises(HostnameException):
        validate_private_url(url)


@pytest.mark.parametrize("url", [
    "http://192.167.0.12",
    "http://11.0.0.1",
    "https://173.25.0.1",
    "https://193.24.23.100",
    "ftp://173.168.1.100/",
    "scp://194.168.1.100/",
    "http://www.google.com/",
    "http://1.1.1.1/",
])
def test_validate_good_destination_address(url):
    assert validate_private_url(url) is None
