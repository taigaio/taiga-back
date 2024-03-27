# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import AppConfig
from django.apps import apps
from django.urls import include, path

from .routers import router


class StatsAppConfig(AppConfig):
    name = "taiga.stats"
    verbose_name = "Stats"

    def ready(self):
        from taiga.urls import urlpatterns
        urlpatterns.append(path('api/v1/', include(router.urls)))
