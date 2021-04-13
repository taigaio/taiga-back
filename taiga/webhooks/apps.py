# -*- coding: utf-8 -*-
from django.apps import apps
from django.apps import AppConfig
from django.db.models import signals


def connect_webhooks_signals():
    from . import signal_handlers as handlers
    signals.post_save.connect(handlers.on_new_history_entry,
                              sender=apps.get_model("history", "HistoryEntry"),
                              dispatch_uid="webhooks")


def disconnect_webhooks_signals():
    signals.post_save.disconnect(sender=apps.get_model("history", "HistoryEntry"), dispatch_uid="webhooks")


class WebhooksAppConfig(AppConfig):
    name = "taiga.webhooks"
    verbose_name = "Webhooks App Config"

    def ready(self):
        connect_webhooks_signals()
