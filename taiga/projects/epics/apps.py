# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
