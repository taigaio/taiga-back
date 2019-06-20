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


import collections

from django.db import connection
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from taiga.base.utils import json
from taiga.base.utils.db import get_typename_for_model_instance
from . import middleware as mw
from . import backends
from taiga.front.templatetags.functions import resolve
from taiga.projects.history.choices import HistoryType


def emit_event(data:dict, routing_key:str, *,
               sessionid:str=None, channel:str="events",
               on_commit:bool=True):
    if not sessionid:
        sessionid = mw.get_current_session_id()

    data = {"session_id": sessionid,
            "data": data}

    backend = backends.get_events_backend()

    def backend_emit_event():
        backend.emit_event(message=json.dumps(data), routing_key=routing_key, channel=channel)

    if on_commit:
        connection.on_commit(backend_emit_event)
    else:
        backend_emit_event()


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

    if app_name in settings.INSTALLED_APPS:
        routing_key = "%s.%s" % (routing_key, model_name)

    data = {"type": type,
            "matches": content_type,
            "pk": pk}

    return emit_event(routing_key=routing_key,
                      channel=channel,
                      sessionid=sessionid,
                      data=data)


def emit_event_for_user_notification(user_id,
                                     *,
                                     session_id: str=None,
                                     event_type: str=None,
                                     data: dict=None):
    """
    Sends a user notification event.
    """
    return emit_event(
        data,
        "web_notifications.{}".format(user_id),
        sessionid=session_id
    )


def emit_live_notification_for_model(obj, user, history, *, type:str="change", channel:str="events",
                                     sessionid:str="not-existing"):
    """
    Sends a model live notification to users.
    """

    if obj._importing:
        return None

    content_type = get_typename_for_model_instance(obj)
    if content_type == "userstories.userstory":
        if history.type == HistoryType.create:
            title = _("User story created")
            url = resolve("userstory", obj.project.slug, obj.ref)
        elif history.type == HistoryType.change:
            title = _("User story changed")
            url = resolve("userstory", obj.project.slug, obj.ref)
        else:
            title = _("User story deleted")
            url = None
        body = _("US #{} - {}").format(obj.ref, obj.subject)
    elif content_type == "tasks.task":
        if history.type == HistoryType.create:
            title = _("Task created")
            url = resolve("task", obj.project.slug, obj.ref)
        elif history.type == HistoryType.change:
            title = _("Task changed")
            url = resolve("task", obj.project.slug, obj.ref)
        else:
            title = _("Task deleted")
            url = None
        body = _("Task #{} - {}").format(obj.ref, obj.subject)
    elif content_type == "issues.issue":
        if history.type == HistoryType.create:
            title = _("Issue created")
            url = resolve("issue", obj.project.slug, obj.ref)
        elif history.type == HistoryType.change:
            title = _("Issue changed")
            url = resolve("issue", obj.project.slug, obj.ref)
        else:
            title = _("Issue deleted")
            url = None
        body = _("Issue: #{} - {}").format(obj.ref, obj.subject)
    elif content_type == "wiki.wiki_page":
        if history.type == HistoryType.create:
            title = _("Wiki Page created")
            url = resolve("wiki", obj.project.slug, obj.slug)
        elif history.type == HistoryType.change:
            title = _("Wiki Page changed")
            url = resolve("wiki", obj.project.slug, obj.slug)
        else:
            title = _("Wiki Page deleted")
            url = None
        body = _("Wiki Page: {}").format(obj.slug)
    elif content_type == "milestones.milestone":
        if history.type == HistoryType.create:
            title = _("Sprint created")
            url = resolve("taskboard", obj.project.slug, obj.slug)
        elif history.type == HistoryType.change:
            title = _("Sprint changed")
            url = resolve("taskboard", obj.project.slug, obj.slug)
        else:
            title = _("Sprint deleted")
            url = None
        body = _("Sprint: {}").format(obj.name)
    else:
        return None

    return emit_event(
        {
            "title": title,
            "body": "Project: {}\n{}".format(obj.project.name, body),
            "url": url,
            "timeout": 10000,
            "id": history.id
        },
        "live_notifications.{}".format(user.id),
        sessionid=sessionid
    )

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
