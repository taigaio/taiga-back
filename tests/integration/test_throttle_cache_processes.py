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


_REDIS_URL = os.environ.get("TAIGA_TEST_THROTTLE_REDIS_URL")
_BACKENDS = ["file"] + (["redis"] if _REDIS_URL else [])


@pytest.mark.parametrize("backend", _BACKENDS)
def test_auth_throttle_is_shared_between_processes(tmp_path, backend):
    prefix = "taiga-throttle-test-" + uuid.uuid4().hex
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    env = os.environ.copy()
    env.update({
        "DJANGO_SETTINGS_MODULE": "tests.config",
        "TAIGA_THROTTLE_TEST_BACKEND": backend,
        "TAIGA_THROTTLE_TEST_CACHE_DIR": str(cache_dir),
        "TAIGA_THROTTLE_TEST_KEY_PREFIX": prefix,
    })
    if backend == "redis":
        env["TAIGA_THROTTLE_TEST_REDIS_URL"] = _REDIS_URL

    worker = r'''
import json
import os
import sys

import django
django.setup()

from django.conf import settings

# Configure rates before importing throttle classes, which bind these defaults.
settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login-fail"] = "2/min"

from django.core.cache import caches
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from taiga.auth.throttling import LoginFailRateThrottle

backend = os.environ["TAIGA_THROTTLE_TEST_BACKEND"]
if backend == "file":
    throttle_cache = {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.environ["TAIGA_THROTTLE_TEST_CACHE_DIR"],
        "KEY_PREFIX": os.environ["TAIGA_THROTTLE_TEST_KEY_PREFIX"],
    }
else:
    throttle_cache = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ["TAIGA_THROTTLE_TEST_REDIS_URL"],
        "KEY_PREFIX": os.environ["TAIGA_THROTTLE_TEST_KEY_PREFIX"],
        "OPTIONS": {"IGNORE_EXCEPTIONS": False},
    }

local_cache = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "throttle-test-local-default",
}
addresses = json.loads(sys.argv[2])

with override_settings(
    CACHES={"default": local_cache, "throttling": throttle_cache},
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

    phase = sys.argv[1]
    try:
        if phase == "a":
            statuses = [login(addresses[0])]
        elif phase == "b":
            statuses = [login(addresses[0]), login(addresses[0]), login(addresses[1])]
        else:
            statuses = []
    finally:
        if phase == "cleanup":
            cache = caches["throttling"]
            for address in addresses:
                try:
                    cache.delete("throttle_login-fail_" + address)
                except Exception:
                    pass

    print(json.dumps(statuses))
'''
    addresses = ["198.51.100.47", "198.51.100.48"]
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def run(phase):
        result = subprocess.run(
            [sys.executable, "-c", worker, phase, json.dumps(addresses)],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, "throttle worker failed"
        return json.loads(result.stdout.splitlines()[-1])

    try:
        first = run("a")
        second = run("b")
        assert first == [400]
        assert second == [400, 429, 400]
    finally:
        try:
            run("cleanup")
        except Exception:
            pass
