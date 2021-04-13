#
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
