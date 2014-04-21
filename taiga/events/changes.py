# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

import json

from django.contrib.contenttypes.models import ContentType
from . import backends

# The complete list of content types
# of allowed models for change events
watched_types = (
    ("userstories", "userstory"),
    ("issues", "issue"),
)


def _get_type_for_model(model_instance):
    """
    Get content type tuple from model instance.
    """
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

