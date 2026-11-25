# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from types import SimpleNamespace

import pytest
from django.core.cache import caches
from django.core.cache.backends.locmem import LocMemCache
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

from taiga.auth.throttling import LoginFailRateThrottle
from taiga.base.api.throttling import SimpleRateThrottle


def test_default_throttle_cache_is_usable(settings, rf):
    class DefaultCacheThrottle(SimpleRateThrottle):
        scope = "login-fail"
        rate = "1/min"

        def get_cache_key(self, request, view):
            return "throttle-default-cache-compatibility"

    assert settings.THROTTLE_CACHE_ALIAS == "default"
    throttle = DefaultCacheThrottle()
    cache = caches["default"]
    cache.delete("throttle-default-cache-compatibility")
    try:
        assert throttle.allow_request(rf.post("/"), None)
        assert not throttle.allow_request(rf.post("/"), None)
    finally:
        cache.delete("throttle-default-cache-compatibility")


def test_throttle_resolves_alias_lazily_when_disabled(settings, rf):
    class DisabledThrottle(LoginFailRateThrottle):
        rate = None

    settings.THROTTLE_CACHE_ALIAS = "missing"
    throttle = DisabledThrottle()

    assert throttle.allow_request(rf.post("/"), SimpleNamespace(action="create"))


def test_active_throttle_does_not_fall_back_for_invalid_alias(settings, rf):
    class ActiveThrottle(LoginFailRateThrottle):
        rate = "1/min"

    settings.THROTTLE_CACHE_ALIAS = "missing"
    throttle = ActiveThrottle()

    with pytest.raises(ImproperlyConfigured):
        throttle.allow_request(rf.post("/"), SimpleNamespace(action="create"))


def test_derived_throttle_can_override_cache(settings):
    class CustomCacheThrottle(LoginFailRateThrottle):
        cache = LocMemCache("custom", {})

    settings.THROTTLE_CACHE_ALIAS = "missing"

    assert isinstance(CustomCacheThrottle().cache, LocMemCache)


def test_throttle_history_expires_with_controlled_timer(settings, rf, tmp_path):
    class TimedThrottle(LoginFailRateThrottle):
        rate = "1/s"

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": str(tmp_path / "default"),
        },
        "throttling": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": str(tmp_path / "throttling"),
        },
    }
    settings.THROTTLE_CACHE_ALIAS = "throttling"
    throttle = TimedThrottle()
    now = [10]
    throttle.timer = lambda: now[0]
    request = rf.post("/")
    view = SimpleNamespace(action="create")

    try:
        assert throttle.allow_request(request, view)
        throttle.finalize(request, HttpResponse(status=400), view)
        assert not throttle.allow_request(request, view)
        now[0] += 2
        assert throttle.allow_request(request, view)
    finally:
        throttle.cache.delete(throttle.get_cache_key(request, view))
