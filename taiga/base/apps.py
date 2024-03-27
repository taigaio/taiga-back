# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import AppConfig


class BaseAppConfig(AppConfig):
    name = "taiga.base"
    verbose_name = "Base App Config"

    def ready(self):
        from .signals.thumbnails import connect_thumbnail_signals
        from .signals.cleanup_files import connect_cleanup_files_signals

        connect_thumbnail_signals()
        connect_cleanup_files_signals()
