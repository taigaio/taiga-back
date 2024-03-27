# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
