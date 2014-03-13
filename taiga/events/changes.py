import json

from django.contrib.contenttypes.models import ContentType
from . import backends

watched_types = (
    ("userstories", "userstory"),
    ("issues", "issue"),
)


def _get_type_for_model(model_instance):
    ct = ContentType.objects.get_for_model(model_instance)
    return (ct.app_label, ct.model)


def emit_change_event_for_model(model_instance, sessionid:str, *,
                                type:str="change", channel:str="events"):
    """
    Emit change event for notify of model change to
    all connected frontends.
    """
    content_type = _get_type_for_model(model_instance)

    assert hasattr(model_instance, "project_id")
    assert content_type in watched_types
    assert type in ("create", "change", "delete")

    project_id = model_instance.project_id
    routing_key = "project.{0}".format(project_id)

    data = {"type": "model-changes",
            "routing_key": routing_key,
            "session_id": sessionid,
            "data": {
                "type": type,
                "matches": ".".join(content_type),
                "pk": model_instance.pk}}

    backend = backends.get_events_backend()
    return backend.emit_event(json.dumps(data), channel="events")

