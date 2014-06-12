# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from functools import partial

from django.db.models.loading import get_model
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

from djmail import template_mail

from taiga.base import exceptions as exc
from taiga.base.utils.text import strip_lines
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType


def notify_policy_exists(project, user) -> bool:
    """
    Check if policy exists for specified project
    and user.
    """
    model_cls = get_model("notifications", "NotifyPolicy")
    qs = model_cls.objects.filter(project=project,
                                  user=user)
    return qs.exists()


def create_notify_policy(project, user, level=NotifyLevel.notwatch):
    """
    Given a project and user, create notification policy for it.
    """
    model_cls = get_model("notifications", "NotifyPolicy")
    try:
        return model_cls.objects.create(project=project,
                                        user=user,
                                        notify_level=level)
    except IntegrityError as e:
        raise exc.IntegrityError("Notify exists for specified user and project") from e


def get_notify_policy(project, user):
    """
    Get notification level for specified project and user.
    """
    model_cls = get_model("notifications", "NotifyPolicy")
    instance, _ = model_cls.objects.get_or_create(project=project, user=user,
                                                  defaults={"notify_level": NotifyLevel.notwatch})
    return instance


def attach_notify_policy_to_project_queryset(current_user, queryset):
    """
    Function that attach "notify_level" attribute on each queryset
    result for query notification level of current user for each
    project in the most efficient way.
    """

    sql = strip_lines("""
    COALESCE((SELECT notifications_notifypolicy.notify_level
             FROM notifications_notifypolicy
             WHERE notifications_notifypolicy.project_id = projects_project.id
               AND notifications_notifypolicy.user_id = {userid}), {default_level})
    """)

    sql = sql.format(userid=current_user.pk,
                     default_level=NotifyLevel.notwatch)
    return queryset.extra(select={"notify_level": sql})


def analize_object_for_watchers(obj:object, history:object):
    """
    Generic implementation for analize model objects and
    extract mentions from it and add it to watchers.
    """
    from taiga import mdrender as mdr

    texts = (getattr(obj, "description", ""),
             getattr(obj, "content", ""),
             getattr(history, "comment", ""),)

    _, data = mdr.render_and_extract(obj.get_project(), "\n".join(texts))

    if data["mentions"]:
        for user in data["mentions"]:
            obj.watchers.add(user)


def get_users_to_notify(obj, *, history) -> list:
    """
    Get filtered set of users to notify for specified
    model instance and changer.

    NOTE: changer at this momment is not used.
    NOTE: analogouts to obj.get_watchers_to_notify(changer)
    """
    project = obj.get_project()

    def _check_level(project:object, user:object, levels:tuple) -> bool:
        policy = get_notify_policy(project, user)
        return policy.notify_level in [int(x) for x in levels]

    _can_notify_hard = partial(_check_level, project,
                               levels=[NotifyLevel.watch])
    _can_notify_light = partial(_check_level, project,
                                levels=[NotifyLevel.watch, NotifyLevel.notwatch])

    candidates = set()
    candidates.update(filter(_can_notify_hard, project.members.all()))
    candidates.update(filter(_can_notify_light, obj.get_watchers()))
    candidates.update(filter(_can_notify_light, obj.get_participants()))

    # Remove the changer from candidates
    candidates.discard(history.owner)

    return frozenset(candidates)


def _resolve_template_name(obj, *, change_type:int) -> str:
    """
    Ginven an changed model instance and change type,
    return the preformated template name for it.
    """
    ct = ContentType.objects.get_for_model(obj.__class__)

    # Resolve integer enum value from "change_type"
    # parameter to human readable string
    if change_type == HistoryType.create:
        change_type = "create"
    elif change_type == HistoryType.change:
        change_type = "change"
    else:
        change_type = "delete"

    tmpl = "{app_label}/{model}-{change}"
    return tmpl.format(app_label=ct.app_label,
                       model=ct.model,
                       change=change_type)


def _make_template_mail(name:str):
    """
    Helper that creates a adhoc djmail template email
    instance for specified name, and return an instance
    of it.
    """
    cls = type("TemplateMail",
               (template_mail.TemplateMail,),
               {"name": name})

    return cls()


def send_notifications(obj, *, history, users):
    """
    Given changed instance, history entry and
    a complete list for users to notify, send
    email to all users.
    """
    context = {"object": obj,
               "changer": history.owner,
               "comment": history.comment,
               "changed_fields": history.values_diff}

    template_name = _resolve_template_name(obj, change_type=history.type)
    email = _make_template_mail(template_name)

    for user in users:
        email.send(user.email, context)
