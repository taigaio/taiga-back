# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url


class FeedbackAppConfig(AppConfig):
    name = "taiga.feedback"
    verbose_name = "Feedback"

    def ready(self):
        if settings.FEEDBACK_ENABLED:
            from taiga.urls import urlpatterns
            from .routers import router
            urlpatterns.append(url(r'^api/v1/', include(router.urls)))
