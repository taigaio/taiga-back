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

from django.apps import apps
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.utils.translation import ugettext as _

from djmail import template_mail

from taiga.base import exceptions as exc
from taiga.base.utils.text import strip_lines
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import (make_key_from_model_object,
                                             get_last_snapshot_for_key,
                                             get_model_from_key)
from taiga.permissions.service import user_has_perm
from taiga.users.models import User

from .models import HistoryChangeNotification


def notify_policy_exists(project, user) -> bool:
    """
    Check if policy exists for specified project
    and user.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
    qs = model_cls.objects.filter(project=project,
                                  user=user)
    return qs.exists()


def create_notify_policy(project, user, level=NotifyLevel.notwatch):
    """
    Given a project and user, create notification policy for it.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
    try:
        return model_cls.objects.create(project=project,
                                        user=user,
                                        notify_level=level)
    except IntegrityError as e:
        raise exc.IntegrityError(_("Notify exists for specified user and project")) from e


def create_notify_policy_if_not_exists(project, user, level=NotifyLevel.notwatch):
    """
    Given a project and user, create notification policy for it.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
    try:
        result = model_cls.objects.get_or_create(project=project,
                                               user=user,
                                               defaults={"notify_level": level})
        return result[0]
    except IntegrityError as e:
        raise exc.IntegrityError(_("Notify exists for specified user and project")) from e


def get_notify_policy(project, user):
    """
    Get notification level for specified project and user.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
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

    # Adding the person who edited the object to the watchers
    if history.comment and not history.owner.is_system:
        obj.watchers.add(history.owner)

def _filter_by_permissions(obj, user):
    UserStory = apps.get_model("userstories", "UserStory")
    Issue = apps.get_model("issues", "Issue")
    Task = apps.get_model("tasks", "Task")
    WikiPage = apps.get_model("wiki", "WikiPage")

    if isinstance(obj, UserStory):
        return user_has_perm(user, "view_us", obj)
    elif isinstance(obj, Issue):
        return user_has_perm(user, "view_issues", obj)
    elif isinstance(obj, Task):
        return user_has_perm(user, "view_tasks", obj)
    elif isinstance(obj, WikiPage):
        return user_has_perm(user, "view_wiki_pages", obj)
    return False


def _filter_notificable(user):
    return user.is_active and not user.is_system


def get_users_to_notify(obj, *, discard_users=None) -> list:
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
    if discard_users:
        candidates = candidates - set(discard_users)

    candidates = filter(partial(_filter_by_permissions, obj), candidates)
    # Filter disabled and system users
    candidates = filter(partial(_filter_notificable), candidates)
    return frozenset(candidates)


def _resolve_template_name(model:object, *, change_type:int) -> str:
    """
    Ginven an changed model instance and change type,
    return the preformated template name for it.
    """
    ct = ContentType.objects.get_for_model(model)
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
    cls = type("InlineCSSTemplateMail",
               (template_mail.InlineCSSTemplateMail,),
               {"name": name})

    return cls()


@transaction.atomic
def send_notifications(obj, *, history):
    if history.is_hidden:
        return None

    key = make_key_from_model_object(obj)
    owner = User.objects.get(pk=history.user["pk"])
    notification, created = (HistoryChangeNotification.objects.select_for_update()
                             .get_or_create(key=key,
                                            owner=owner,
                                            project=obj.project,
                                            history_type = history.type))

    notification.updated_datetime = timezone.now()
    notification.save()
    notification.history_entries.add(history)

    # Get a complete list of notifiable users for current
    # object and send the change notification to them.
    notify_users = get_users_to_notify(obj, discard_users=[notification.owner])
    for notify_user in notify_users:
        notification.notify_users.add(notify_user)

    # If we are the min interval is 0 it just work in a synchronous and spamming way
    if settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL == 0:
        send_sync_notifications(notification.id)

@transaction.atomic
def send_sync_notifications(notification_id):
    """
    Given changed instance, calculate the history entry and
    a complete list for users to notify, send
    email to all users.
    """

    notification = HistoryChangeNotification.objects.select_for_update().get(pk=notification_id)
    # If the las modification is too recent we ignore it
    now = timezone.now()
    time_diff = now - notification.updated_datetime
    if time_diff.seconds < settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL:
        return

    history_entries = tuple(notification.history_entries.all().order_by("created_at"))
    obj, _ = get_last_snapshot_for_key(notification.key)
    obj_class = get_model_from_key(obj.key)

    context = {"obj_class": obj_class,
               "snapshot": obj.snapshot,
               "project": notification.project,
               "changer": notification.owner,
               "history_entries": history_entries}

    model = get_model_from_key(notification.key)
    template_name = _resolve_template_name(model, change_type=notification.history_type)
    email = _make_template_mail(template_name)

    for user in notification.notify_users.distinct():
        context["user"] = user
        context["lang"] = user.lang or settings.LANGUAGE_CODE
        email.send(user.email, context)

    notification.delete()


def process_sync_notifications():
    for notification in HistoryChangeNotification.objects.all():
        send_sync_notifications(notification.pk)
