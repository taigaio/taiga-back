# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.apps import apps
from django.conf.urls import include, url

from .routers import router


class StatsAppConfig(AppConfig):
    name = "taiga.stats"
    verbose_name = "Stats"

    def ready(self):
        from taiga.urls import urlpatterns
        urlpatterns.append(url(r'^api/v1/', include(router.urls)))
