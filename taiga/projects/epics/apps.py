# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import AppConfig
from django.apps import apps
from django.db.models import signals


def connect_epics_signals():
    from taiga.projects.tagging import signals as tagging_handlers

    # Tags
    signals.pre_save.connect(tagging_handlers.tags_normalization,
                             sender=apps.get_model("epics", "Epic"),
                             dispatch_uid="tags_normalization_epic")


def connect_epics_custom_attributes_signals():
    from taiga.projects.custom_attributes import signals as custom_attributes_handlers
    signals.post_save.connect(custom_attributes_handlers.create_custom_attribute_value_when_create_epic,
                              sender=apps.get_model("epics", "Epic"),
                              dispatch_uid="create_custom_attribute_value_when_create_epic")


def connect_all_epics_signals():
    connect_epics_signals()
    connect_epics_custom_attributes_signals()


def disconnect_epics_signals():
    signals.pre_save.disconnect(sender=apps.get_model("epics", "Epic"),
                                dispatch_uid="tags_normalization")


def disconnect_epics_custom_attributes_signals():
    signals.post_save.disconnect(sender=apps.get_model("epics", "Epic"),
                                 dispatch_uid="create_custom_attribute_value_when_create_epic")


def disconnect_all_epics_signals():
    disconnect_epics_signals()
    disconnect_epics_custom_attributes_signals()


class EpicsAppConfig(AppConfig):
    name = "taiga.projects.epics"
    verbose_name = "Epics"

    def ready(self):
        connect_all_epics_signals()
