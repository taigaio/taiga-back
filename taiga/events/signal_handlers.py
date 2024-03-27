# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from django.apps import apps
from taiga.base.utils.db import get_typename_for_model_instance

from . import middleware as mw
from . import events


def on_save_any_model(sender, instance, created, **kwargs):
    # Ignore any object that can not have project_id
    if not hasattr(instance, "project_id"):
        return
    content_type = get_typename_for_model_instance(instance)

    # Ignore any other events
    app_config = apps.get_app_config('events')
    if content_type not in app_config.events_watched_types:
        return

    sesionid = mw.get_current_session_id()
    type = "create" if created else "change"

    events.emit_event_for_model(instance, sessionid=sesionid, type=type)


def on_delete_any_model(sender, instance, **kwargs):
    # Ignore any object that can not have project_id
    content_type = get_typename_for_model_instance(instance)

    # Ignore any other changes
    app_config = apps.get_app_config('events')
    if content_type not in app_config.events_watched_types:
        return

    sesionid = mw.get_current_session_id()

    events.emit_event_for_model(instance, sessionid=sesionid, type="delete")
