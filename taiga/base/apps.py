# -*- coding: utf-8 -*-
from django.apps import AppConfig


class BaseAppConfig(AppConfig):
    name = "taiga.base"
    verbose_name = "Base App Config"

    def ready(self):
        from .signals.thumbnails import connect_thumbnail_signals
        from .signals.cleanup_files import connect_cleanup_files_signals

        connect_thumbnail_signals()
        connect_cleanup_files_signals()
