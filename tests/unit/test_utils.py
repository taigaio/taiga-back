from unittest import mock

import django_sites as sites

from taiga.base.utils.urls import get_absolute_url, is_absolute_url, build_url
from taiga.base.utils.db import save_in_bulk


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
