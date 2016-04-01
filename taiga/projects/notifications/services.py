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

import datetime

from functools import partial

from django.apps import apps
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.base.mails import InlineCSSTemplateMail
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import (make_key_from_model_object,
                                             get_last_snapshot_for_key,
                                             get_model_from_key)
from taiga.permissions.service import user_has_perm

from .models import HistoryChangeNotification, Watched


def notify_policy_exists(project, user) -> bool:
    """
    Check if policy exists for specified project
    and user.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
    qs = model_cls.objects.filter(project=project,
                                  user=user)
    return qs.exists()


def create_notify_policy(project, user, level=NotifyLevel.involved):
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


def create_notify_policy_if_not_exists(project, user, level=NotifyLevel.involved):
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
                                                  defaults={"notify_level": NotifyLevel.involved})
    return instance


def analize_object_for_watchers(obj:object, comment:str, user:object):
    """
    Generic implementation for analize model objects and
    extract mentions from it and add it to watchers.
    """

    if not hasattr(obj, "get_project"):
        return

    if not hasattr(obj, "add_watcher"):
        return


    texts = (getattr(obj, "description", ""),
             getattr(obj, "content", ""),
             comment,)

    from taiga.mdrender.service import render_and_extract
    _, data = render_and_extract(obj.get_project(), "\n".join(texts))

    if data["mentions"]:
        for user in data["mentions"]:
            obj.add_watcher(user)

    # Adding the person who edited the object to the watchers
    if comment and not user.is_system:
        obj.add_watcher(user)


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
        return policy.notify_level in levels

    _can_notify_hard = partial(_check_level, project,
                               levels=[NotifyLevel.all])
    _can_notify_light = partial(_check_level, project,
                                levels=[NotifyLevel.all, NotifyLevel.involved])

    candidates = set()
    candidates.update(filter(_can_notify_hard, project.members.all()))
    candidates.update(filter(_can_notify_hard, obj.project.get_watchers()))
    candidates.update(filter(_can_notify_light, obj.get_watchers()))
    candidates.update(filter(_can_notify_light, obj.get_participants()))

    # Remove the changer from candidates
    if discard_users:
        candidates = candidates - set(discard_users)

    candidates = set(filter(partial(_filter_by_permissions, obj), candidates))
    # Filter disabled and system users
    candidates = set(filter(partial(_filter_notificable), candidates))
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
               (InlineCSSTemplateMail,),
               {"name": name})

    return cls()


@transaction.atomic
def send_notifications(obj, *, history):
    if history.is_hidden:
        return None

    key = make_key_from_model_object(obj)
    owner = get_user_model().objects.get(pk=history.user["pk"])
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
    # If the last modification is too recent we ignore it
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
    domain = settings.SITES["api"]["domain"].split(":")[0] or settings.SITES["api"]["domain"]

    if "ref" in obj.snapshot:
        msg_id = obj.snapshot["ref"]
    elif "slug" in obj.snapshot:
        msg_id = obj.snapshot["slug"]
    else:
        msg_id = 'taiga-system'

    now = datetime.datetime.now()
    format_args = {"project_slug": notification.project.slug,
                   "project_name": notification.project.name,
                   "msg_id": msg_id,
                   "time": int(now.timestamp()),
                   "domain": domain}

    headers = {"Message-ID": "<{project_slug}/{msg_id}/{time}@{domain}>".format(**format_args),
               "In-Reply-To": "<{project_slug}/{msg_id}@{domain}>".format(**format_args),
               "References": "<{project_slug}/{msg_id}@{domain}>".format(**format_args),

               "List-ID": 'Taiga/{project_name} <taiga.{project_slug}@{domain}>'.format(**format_args),

               "Thread-Index": make_ms_thread_index("<{project_slug}/{msg_id}@{domain}>".format(**format_args), now)}

    for user in notification.notify_users.distinct():
        context["user"] = user
        context["lang"] = user.lang or settings.LANGUAGE_CODE
        email.send(user.email, context, headers=headers)

    notification.delete()


def process_sync_notifications():
    for notification in HistoryChangeNotification.objects.all():
        send_sync_notifications(notification.pk)


def _get_q_watchers(obj):
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    return Q(watched__content_type=obj_type, watched__object_id=obj.id)


def get_watchers(obj):
    """Get the watchers of an object.

    :param obj: Any Django model instance.

    :return: User queryset object representing the users that watch the object.
    """
    return get_user_model().objects.filter(_get_q_watchers(obj))


def get_related_people(obj):
    """Get the related people of an object for notifications.

    :param obj: Any Django model instance.

    :return: User queryset object representing the users related to the object.
    """
    related_people_q = Q()

    ## - Owner
    if hasattr(obj, "owner_id") and obj.owner_id:
        related_people_q.add(Q(id=obj.owner_id), Q.OR)

    ## - Assigned to
    if hasattr(obj, "assigned_to_id") and obj.assigned_to_id:
        related_people_q.add(Q(id=obj.assigned_to_id), Q.OR)

    ## - Watchers
    related_people_q.add(_get_q_watchers(obj), Q.OR)

    ## - Apply filters
    related_people = get_user_model().objects.filter(related_people_q)

    ## - Exclude inactive and system users and remove duplicate
    related_people = related_people.exclude(is_active=False)
    related_people = related_people.exclude(is_system=True)
    related_people = related_people.distinct()
    return related_people


def get_watched(user_or_id, model):
    """Get the objects watched by an user.

    :param user_or_id: :class:`~taiga.users.models.User` instance or id.
    :param model: Show only objects of this kind. Can be any Django model class.

    :return: Queryset of objects representing the votes of the user.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    conditions = ('notifications_watched.content_type_id = %s',
                  '%s.id = notifications_watched.object_id' % model._meta.db_table,
                  'notifications_watched.user_id = %s')

    if isinstance(user_or_id, get_user_model()):
        user_id = user_or_id.id
    else:
        user_id = user_or_id

    return model.objects.extra(where=conditions, tables=('notifications_watched',),
                               params=(obj_type.id, user_id))


def get_projects_watched(user_or_id):
    """Get the objects watched by an user.

    :param user_or_id: :class:`~taiga.users.models.User` instance or id.
    :param model: Show only objects of this kind. Can be any Django model class.

    :return: Queryset of objects representing the votes of the user.
    """

    if isinstance(user_or_id, get_user_model()):
        user = user_or_id
    else:
        user = get_user_model().objects.get(id=user_or_id)

    project_class = apps.get_model("projects", "Project")
    project_ids = user.notify_policies.exclude(notify_level=NotifyLevel.none).values_list("project__id", flat=True)
    return project_class.objects.filter(id__in=project_ids)

def add_watcher(obj, user):
    """Add a watcher to an object.

    If the user is already watching the object nothing happents (except if there is a level update),
    so this function can be considered idempotent.

    :param obj: Any Django model instance.
    :param user: User adding the watch. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    watched, created = Watched.objects.get_or_create(content_type=obj_type,
        object_id=obj.id, user=user, project=obj.project)

    notify_policy, _ = apps.get_model("notifications", "NotifyPolicy").objects.get_or_create(
        project=obj.project, user=user, defaults={"notify_level": NotifyLevel.involved})

    return watched


def remove_watcher(obj, user):
    """Remove an watching user from an object.

    If the user has not watched the object nothing happens so this function can be considered
    idempotent.

    :param obj: Any Django model instance.
    :param user: User removing the watch. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    qs = Watched.objects.filter(content_type=obj_type, object_id=obj.id, user=user)
    if not qs.exists():
        return

    qs.delete()


def set_notify_policy_level(notify_policy, notify_level):
    """
    Set notification level for specified policy.
    """
    if not notify_level in [e.value for e in NotifyLevel]:
        raise exc.IntegrityError(_("Invalid value for notify level"))

    notify_policy.notify_level = notify_level
    notify_policy.save()


def set_notify_policy_level_to_ignore(notify_policy):
    """
    Set notification level for specified policy.
    """
    set_notify_policy_level(notify_policy, NotifyLevel.none)


def make_ms_thread_index(msg_id, dt):
    """
    Create the 22-byte base of the thread-index string in the format:

    6 bytes = First 6 significant bytes of the FILETIME stamp
    16 bytes = GUID (we're using a md5 hash of the message id)

    See http://www.meridiandiscovery.com/how-to/e-mail-conversation-index-metadata-computer-forensics/
    """

    import base64
    import hashlib
    import struct

    # Convert to FILETIME epoch (microseconds since 1601)
    delta = datetime.date(1970, 1, 1) - datetime.date(1601, 1, 1)
    filetime = int(dt.timestamp() + delta.total_seconds()) * 10000000

    # only want the first 6 bytes
    thread_bin = struct.pack(">Q", filetime)[:6]

    # Make a guid. This is usually generated by Outlook.
    # The format is usually >IHHQ, but we don't care since it's just a hash of the id
    md5 = hashlib.md5(msg_id.encode('utf-8'))
    thread_bin += md5.digest()

    # base64 encode
    return base64.b64encode(thread_bin).decode("utf-8")
