# Copyright (C) 2014-2019 Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.apps import apps, AppConfig
from django.db.models import signals


def connect_events_signals():
    from . import signal_handlers as handlers
    signals.post_save.connect(handlers.on_save_any_model, dispatch_uid="events_change")
    signals.post_delete.connect(handlers.on_delete_any_model, dispatch_uid="events_delete")


def disconnect_events_signals():
    signals.post_save.disconnect(dispatch_uid="events_change")
    signals.post_delete.disconnect(dispatch_uid="events_delete")


class EventsAppConfig(AppConfig):
    name = "taiga.events"
    verbose_name = "Events App Config"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events_watched_types = set()

    def ready(self):
        connect_events_signals()
        for config in apps.get_app_configs():
            if not hasattr(config, 'watched_types'):
                continue

            self.events_watched_types = self.events_watched_types.union(config.watched_types)
