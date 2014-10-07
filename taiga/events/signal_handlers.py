
from django.db.models import signals
from django.dispatch import receiver

from . import middleware as mw
from . import events


def on_save_any_model(sender, instance, created, **kwargs):
    # Ignore any object that can not have project_id
    content_type = events._get_type_for_model(instance)

    # Ignore any other events
    if content_type not in events.watched_types:
        return

    sesionid = mw.get_current_session_id()

    if created:
        events.emit_event_for_model(instance, sessionid=sesionid, type="create")
    else:
        events.emit_event_for_model(instance, sessionid=sesionid, type="change")


def on_delete_any_model(sender, instance, **kwargs):
    # Ignore any object that can not have project_id
    content_type = events._get_type_for_model(instance)

    # Ignore any other changes
    if content_type not in events.watched_types:
        return

    sesionid = mw.get_current_session_id()
    events.emit_event_for_model(instance, sessionid=sesionid, type="delete")
