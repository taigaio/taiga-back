from django.db.models import signals
from django.dispatch import receiver

from . import middleware as mw
from . import changes


@receiver(signals.post_save, dispatch_uid="events_dispatcher_on_change")
def on_save_any_model(sender, instance, created, **kwargs):
    # Ignore any object that can not have project_id
    content_type = changes._get_type_for_model(instance)

    # Ignore any other changes
    if content_type not in changes.watched_types:
        return

    sesionid = mw.get_current_session_id()

    if created:
        changes.emit_change_event_for_model(instance, sesionid, type="create")
    else:
        changes.emit_change_event_for_model(instance, sesionid, type="change")


@receiver(signals.post_delete, dispatch_uid="events_dispatcher_on_delete")
def on_delete_any_model(sender, instance, **kwargs):
    # Ignore any object that can not have project_id
    content_type = changes._get_type_for_model(instance)

    # Ignore any other changes
    if content_type not in changes.watched_types:
        return

    sesionid = mw.get_current_session_id()
    changes.emit_change_event_for_model(instance, sesionid, type="delete")
