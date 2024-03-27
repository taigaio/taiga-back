# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import AppConfig
from django.apps import apps
from django.conf import settings
from django.urls import include, path


class FeedbackAppConfig(AppConfig):
    name = "taiga.feedback"
    verbose_name = "Feedback"

    def ready(self):
        if settings.FEEDBACK_ENABLED:
            from taiga.urls import urlpatterns
            from .routers import router
            urlpatterns.append(path('api/v1/', include(router.urls)))
