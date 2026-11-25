# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import json
import os
import subprocess
import sys
import uuid

import pytest
from django.core.cache.backends.locmem import LocMemCache


fallback_cache_calls = []


class FallbackDetectingCache(LocMemCache):
    def get(self, key, default=None, version=None):
        fallback_cache_calls.append("get")
        return super().get(key, default, version)

    def set(self, key, value, timeout=None, version=None):
        fallback_cache_calls.append("set")
        return super().set(key, value, timeout, version)


class FailingCache(LocMemCache):
    def __init__(self, location, params):
        super().__init__(location, params)
        self.failure = params["OPTIONS"]["FAILURE"]

    def get(self, key, default=None, version=None):
        if self.failure == "get":
            raise RuntimeError("configured cache read failed")
        return super().get(key, default, version)

    def set(self, key, value, timeout=None, version=None):
        if self.failure == "set":
            raise RuntimeError("configured cache write failed")
        return super().set(key, value, timeout, version)


_REDIS_URL = os.environ.get("TAIGA_TEST_THROTTLE_REDIS_URL")
_BACKENDS = ["file"] + (["redis"] if _REDIS_URL else [])


@pytest.mark.parametrize("backend", _BACKENDS)
def test_auth_throttle_is_shared_between_processes(tmp_path, backend):
    prefix = "taiga-throttle-test-" + uuid.uuid4().hex
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "tests.config"
    throttle_cache = {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(cache_dir),
        "KEY_PREFIX": prefix,
    }
    if backend == "redis":
        throttle_cache = {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_URL,
            "KEY_PREFIX": prefix,
            "OPTIONS": {"IGNORE_EXCEPTIONS": False},
        }
    env["TAIGA_THROTTLE_TEST_CACHES"] = json.dumps({
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "throttle-test-local-default",
        },
        "throttling": throttle_cache,
    })

    worker = r'''
import json
import os
import sys

import django
django.setup()

from django.conf import settings

# Configure rates before importing throttle classes, which bind these defaults.
settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login-fail"] = "2/min"

from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

addresses = sys.argv[1:]

with override_settings(
    CACHES=json.loads(os.environ["TAIGA_THROTTLE_TEST_CACHES"]),
    THROTTLE_CACHE_ALIAS="throttling",
):
    client = Client()
    url = reverse("auth-list")

    def login(ip):
        return client.post(
            url,
            data=json.dumps({"type": "invalid"}),
            content_type="application/json",
            REMOTE_ADDR=ip,
        ).status_code

    statuses = [login(address) for address in addresses]
    print(json.dumps(statuses))
'''
    addresses = ["198.51.100.47", "198.51.100.48"]
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def run(request_ips):
        result = subprocess.run(
            [sys.executable, "-c", worker, *request_ips],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, "throttle worker failed"
        return json.loads(result.stdout.splitlines()[-1])

    first = run([addresses[0]])
    second = run([addresses[0], addresses[0], addresses[1]])
    assert first == [400]
    assert second == [400, 429, 400]


@pytest.mark.parametrize("failure", ["get", "set"])
def test_throttle_cache_errors_return_500_without_default_fallback(settings, monkeypatch, failure):
    from django.test import Client
    from django.urls import reverse

    from taiga.auth.throttling import LoginFailRateThrottle

    monkeypatch.setattr(LoginFailRateThrottle, "THROTTLE_RATES", {"login-fail": "1/min"})
    fallback_cache_calls.clear()
    settings.CACHES = {
        "default": {
            "BACKEND": "tests.integration.test_throttle_cache_processes.FallbackDetectingCache",
            "LOCATION": "throttle-error-default",
        },
        "throttling": {
            "BACKEND": "tests.integration.test_throttle_cache_processes.FailingCache",
            "LOCATION": "throttle-error",
            "OPTIONS": {"FAILURE": failure},
        },
    }
    settings.THROTTLE_CACHE_ALIAS = "throttling"

    response = Client(raise_request_exception=False).post(
        reverse("auth-list"), data=json.dumps({"type": "invalid"}),
        content_type="application/json",
    )

    assert response.status_code == 500
    assert fallback_cache_calls == []
