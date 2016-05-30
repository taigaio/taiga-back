# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
import collections

from django.contrib.contenttypes.models import ContentType

from taiga.base.utils import json
from taiga.base.utils.db import get_typename_for_model_instance
from . import middleware as mw
from . import backends

# The complete list of content types
# of allowed models for change events
watched_types = set([
    "userstories.userstory",
    "issues.issue",
    "tasks.task",
    "wiki.wiki_page",
    "milestones.milestone",
])


def emit_event(data:dict, routing_key:str, *,
               sessionid:str=None, channel:str="events"):
    if not sessionid:
        sessionid = mw.get_current_session_id()

    data = {"session_id": sessionid,
            "data": data}

    backend = backends.get_events_backend()
    return backend.emit_event(message=json.dumps(data),
                              routing_key=routing_key,
                              channel=channel)


def emit_event_for_model(obj, *, type:str="change", channel:str="events",
                         content_type:str=None, sessionid:str=None):
    """
    Sends a model change event.
    """

    if obj._importing:
        return None

    assert type in set(["create", "change", "delete"])
    assert hasattr(obj, "project_id")

    if not content_type:
        content_type = get_typename_for_model_instance(obj)

    projectid = getattr(obj, "project_id")
    pk = getattr(obj, "pk", None)

    app_name, model_name = content_type.split(".", 1)
    routing_key = "changes.project.{0}.{1}".format(projectid, app_name)

    data = {"type": type,
            "matches": content_type,
            "pk": pk}

    return emit_event(routing_key=routing_key,
                      channel=channel,
                      sessionid=sessionid,
                      data=data)


def emit_event_for_ids(ids, content_type:str, projectid:int, *,
                       type:str="change", channel:str="events", sessionid:str=None):
    assert type in set(["create", "change", "delete"])
    assert isinstance(ids, collections.Iterable)
    assert content_type, "'content_type' parameter is mandatory"

    app_name, model_name = content_type.split(".", 1)
    routing_key = "changes.project.{0}.{1}".format(projectid, app_name)

    data = {"type": type,
            "matches": content_type,
            "pk": ids}

    return emit_event(routing_key=routing_key,
                      channel=channel,
                      sessionid=sessionid,
                      data=data)
