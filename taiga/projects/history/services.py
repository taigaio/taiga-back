# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
This module contains a main domain logic for object history management.
This is possible example:

  from taiga.projects import history

  class ViewSet(restfw.ViewSet):
      def create(request):
          object = get_some_object()
          history.freeze(object)
          # Do something...
          history.persist_history(object, user=request.user)
"""
import logging
from collections import namedtuple
from copy import deepcopy
from functools import partial
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import transaction as tx
from django_pglocks import advisory_lock

from taiga.mdrender.service import render as mdrender
from taiga.base.utils.db import get_typename_for_model_class
from taiga.base.utils.diff import make_diff as make_diff_from_dicts

from .models import HistoryType

# Freeze implementatitions
from .freeze_impl import project_freezer
from .freeze_impl import milestone_freezer
from .freeze_impl import epic_freezer
from .freeze_impl import epic_related_userstory_freezer
from .freeze_impl import userstory_freezer
from .freeze_impl import issue_freezer
from .freeze_impl import task_freezer
from .freeze_impl import wikipage_freezer


from .freeze_impl import project_values
from .freeze_impl import milestone_values
from .freeze_impl import epic_values
from .freeze_impl import epic_related_userstory_values
from .freeze_impl import userstory_values
from .freeze_impl import issue_values
from .freeze_impl import task_values
from .freeze_impl import wikipage_values

# Type that represents a freezed object
FrozenObj = namedtuple("FrozenObj", ["key", "snapshot"])
FrozenDiff = namedtuple("FrozenDiff", ["key", "diff", "snapshot"])

# Dict containing registred contentypes with their freeze implementation.
_freeze_impl_map = {}

# Dict containing registred containing with their values implementation.
_values_impl_map = {}

# Not important fields for models (history entries with only
# this fields are marked as hidden).
_not_important_fields = {
    "epics.epic": frozenset(["epics_order", "user_stories"]),
    "userstories.userstory": frozenset(
        ["backlog_order", "sprint_order", "kanban_order"]),
    "tasks.task": frozenset(["us_order", "taskboard_order"]),
}

_deprecated_fields = {
    "userstories.userstory": frozenset(["assigned_to"]),
}

log = logging.getLogger("taiga.history")


def make_key_from_model_object(obj: object) -> str:
    """
    Create unique key from model instance.
    """
    tn = get_typename_for_model_class(obj.__class__)
    return "{0}:{1}".format(tn, obj.pk)


def get_model_from_key(key: str) -> object:
    """
    Get model from key
    """
    class_name, pk = key.split(":", 1)
    return apps.get_model(class_name)


def get_pk_from_key(key: str) -> object:
    """
    Get pk from key
    """
    class_name, pk = key.split(":", 1)
    return pk


def get_instance_from_key(key: str) -> object:
    """
    Get instance from key
    """
    model = get_model_from_key(key)
    pk = get_pk_from_key(key)
    try:
        obj = model.objects.get(pk=pk)
        return obj
    except model.DoesNotExist:
        # Catch simultaneous DELETE request
        return None


def register_values_implementation(typename: str, fn=None):
    """
    Register values implementation for specified typename.
    This function can be used as decorator.
    """

    assert isinstance(typename, str), "typename must be specied"

    if fn is None:
        return partial(register_values_implementation, typename)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    _values_impl_map[typename] = _wrapper
    return _wrapper


def register_freeze_implementation(typename: str, fn=None):
    """
    Register freeze implementation for specified typename.
    This function can be used as decorator.
    """

    assert isinstance(typename, str), "typename must be specied"

    if fn is None:
        return partial(register_freeze_implementation, typename)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    _freeze_impl_map[typename] = _wrapper
    return _wrapper


# Low level api

def freeze_model_instance(obj: object) -> FrozenObj:
    """
    Creates a new frozen object from model instance.

    The freeze process consists on converting model
    instances to hashable plain python objects and
    wrapped into FrozenObj.
    """

    model_cls = obj.__class__

    # Additional query for test if object is really exists
    # on the database or it is removed.
    try:
        obj = model_cls.objects.get(pk=obj.pk)
    except model_cls.DoesNotExist:
        return None

    typename = get_typename_for_model_class(model_cls)
    if typename not in _freeze_impl_map:
        raise RuntimeError("No implementation found for {}".format(typename))

    key = make_key_from_model_object(obj)
    impl_fn = _freeze_impl_map[typename]
    snapshot = impl_fn(obj)
    assert isinstance(snapshot, dict), \
        "freeze handlers should return always a dict"

    return FrozenObj(key, snapshot)


def is_hidden_snapshot(obj: FrozenDiff) -> bool:
    """
    Check if frozen object is considered
    hidden or not.
    """
    content_type, pk = obj.key.rsplit(":", 1)
    snapshot_fields = frozenset(obj.diff.keys())

    if content_type not in _not_important_fields:
        return False

    nfields = _not_important_fields[content_type]
    result = snapshot_fields - nfields

    if snapshot_fields and len(result) == 0:
        return True

    return False


def get_excluded_fields(typename: str) -> tuple:
    """
    Get excluded and deprected fields to avoid in the diff
    """
    return _deprecated_fields.get(typename, ())


def migrate_userstory_diff(obj: FrozenObj) -> FrozenObj:
    # Due to multiple assignment migration, for old snapshots we add a list
    # with the 'assigned to' value
    if 'assigned_users' not in obj.snapshot.keys():
        snapshot = deepcopy(obj.snapshot)
        snapshot['assigned_users'] = [obj.snapshot['assigned_to']] \
            if obj.snapshot['assigned_to'] else []

        obj = FrozenObj(obj.key, snapshot)

    return obj


_migrations = {"userstories.userstory": migrate_userstory_diff}


def migrate_to_last_version(typename: str, obj: FrozenObj) -> FrozenObj:
    """""
    Adapt old snapshots to the last format in order to generate correct diffs.
    :param typename:
    :param obj:
    :return:
    """
    return _migrations.get(typename, lambda x: x)(obj)


def make_diff(oldobj: FrozenObj, newobj: FrozenObj,
              excluded_keys: tuple = ()) -> FrozenDiff:
    """
    Compute a diff between two frozen objects.
    """

    assert isinstance(newobj, FrozenObj), \
        "newobj parameter should be instance of FrozenObj"

    if oldobj is None:
        return FrozenDiff(newobj.key, {}, newobj.snapshot)

    first = oldobj.snapshot
    second = newobj.snapshot

    # The object's attachments are manually handled to avoid considering changes in their URL's token as a user activity
    #   (just when the `taiga-protected` module is enabled)
    diff = make_diff_from_dicts(first, second, None, frozenset().union(excluded_keys, frozenset(["attachments"])))
    attach_diffs = _make_diff_in_attachments(first, second)
    if attach_diffs:
        diff["attachments"] = attach_diffs

    return FrozenDiff(newobj.key, diff, newobj.snapshot)


def _make_diff_in_attachments(first_snapshot, second_snapshot):
    if "attachments" in first_snapshot:
        old_attachments = {x["id"]: x for x in first_snapshot["attachments"]}
        new_attachments = {x["id"]: x for x in second_snapshot["attachments"]}
        snapshot_attachments_tuple = first_snapshot["attachments"], second_snapshot["attachments"]

        for attach_id in set(tuple(old_attachments.keys()) + tuple(new_attachments.keys())):
            if attach_id in old_attachments and attach_id in new_attachments:
                attachments_changed = make_diff_from_dicts(old_attachments[attach_id], new_attachments[attach_id],
                                              excluded_keys=("filename", "url", "thumb_url", "order"))
                if attachments_changed:
                    return snapshot_attachments_tuple
            elif attach_id in old_attachments and attach_id not in new_attachments:
                return snapshot_attachments_tuple
            elif attach_id not in old_attachments and attach_id in new_attachments:
                return snapshot_attachments_tuple

    return None


def make_diff_values(typename: str, fdiff: FrozenDiff) -> dict:
    """
    Given a typename and diff, build a values dict for it.
    If no implementation found for typename, warnig is raised in
    logging and returns empty dict.
    """

    if typename not in _values_impl_map:
        log.warning(
            "No implementation found of '{}' for values.".format(typename))
        return {}

    impl_fn = _values_impl_map[typename]
    return impl_fn(fdiff.diff)


def _rebuild_snapshot_from_diffs(keysnapshot, partials):
    result = deepcopy(keysnapshot)

    for part in partials:
        for key, value in part.diff.items():
            result[key] = value[1]

    return result


def get_last_snapshot_for_key(key: str) -> FrozenObj:
    entry_model = apps.get_model("history", "HistoryEntry")

    # Search last snapshot
    qs = (entry_model.objects
          .filter(key=key, is_snapshot=True)
          .order_by("-created_at"))

    keysnapshot = qs.first()
    if keysnapshot is None:
        return None, True

    # Get all partial snapshots
    entries = tuple(entry_model.objects
                    .filter(key=key, is_snapshot=False)
                    .filter(created_at__gte=keysnapshot.created_at)
                    .order_by("created_at"))

    snapshot = _rebuild_snapshot_from_diffs(keysnapshot.snapshot, entries)
    max_partial_diffs = getattr(settings, "MAX_PARTIAL_DIFFS", 60)

    if len(entries) >= max_partial_diffs:
        return FrozenObj(keysnapshot.key, snapshot), True

    return FrozenObj(keysnapshot.key, snapshot), False


# Public api

def get_modified_fields(obj: object, last_modifications):
    """
    Get the modified fields for an object through his last modifications
    """
    key = make_key_from_model_object(obj)
    entry_model = apps.get_model("history", "HistoryEntry")
    history_entries = (
        entry_model.objects.filter(key=key)
                           .order_by("-created_at")
                           .values_list("diff",
                                        flat=True)[0:last_modifications]
    )

    modified_fields = []
    for history_entry in history_entries:
        modified_fields += history_entry.keys()

    return modified_fields


@tx.atomic
def take_snapshot(obj: object, *, comment: str="", user=None,
                  delete: bool=False):
    """
    Given any model instance with registred content type,
    create new history entry of "change" type.

    This raises exception in case of object wasn't
    previously freezed.
    """

    key = make_key_from_model_object(obj)
    with advisory_lock("history-"+key):
        typename = get_typename_for_model_class(obj.__class__)

        new_fobj = freeze_model_instance(obj)
        old_fobj, need_real_snapshot = get_last_snapshot_for_key(key)

        # migrate diff to latest schema
        if old_fobj:
            old_fobj = migrate_to_last_version(typename, old_fobj)

        entry_model = apps.get_model("history", "HistoryEntry")
        user_id = None if user is None else user.id
        user_name = "" if user is None else user.get_full_name()

        # Determine history type
        if delete:
            entry_type = HistoryType.delete
            need_real_snapshot = True
        elif new_fobj and not old_fobj:
            entry_type = HistoryType.create
        elif new_fobj and old_fobj:
            entry_type = HistoryType.change
        else:
            raise RuntimeError("Unexpected condition")

        excluded_fields = get_excluded_fields(typename)

        fdiff = make_diff(old_fobj, new_fobj, excluded_fields)

        # If diff and comment are empty, do
        # not create empty history entry
        if (not fdiff.diff and
                not comment and old_fobj is not None and
                entry_type != HistoryType.delete):
            return None

        fvals = make_diff_values(typename, fdiff)

        if len(comment) > 0:
            is_hidden = False
        else:
            is_hidden = is_hidden_snapshot(fdiff)

        kwargs = {
            "user": {"pk": user_id, "name": user_name},
            "project_id": getattr(obj, 'project_id', getattr(obj, 'id', None)),
            "key": key,
            "type": entry_type,
            "snapshot": fdiff.snapshot if need_real_snapshot else None,
            "diff": fdiff.diff,
            "values": fvals,
            "comment": comment,
            "comment_html": mdrender(obj.project, comment),
            "is_hidden": is_hidden,
            "is_snapshot": need_real_snapshot,
        }

        return entry_model.objects.create(**kwargs)


# High level query api

def get_history_queryset_by_model_instance(obj: object,
                                           types=(HistoryType.change,),
                                           include_hidden=False):
    """
    Get one page of history for specified object.
    """
    key = make_key_from_model_object(obj)
    history_entry_model = apps.get_model("history", "HistoryEntry")

    qs = history_entry_model.objects.filter(key=key, type__in=types)
    if not include_hidden:
        qs = qs.filter(is_hidden=False)

    return qs.order_by("created_at")


def prefetch_owners_in_history_queryset(qs):
    user_ids = [u["pk"] for u in qs.values_list("user", flat=True)]
    users = get_user_model().objects.filter(id__in=user_ids)
    users_by_id = {u.id: u for u in users}
    for history_entry in qs:
        history_entry.prefetch_owner(users_by_id.get(history_entry.user["pk"],
                                                     None))

    return qs


# Freeze & value register
register_freeze_implementation("projects.project", project_freezer)
register_freeze_implementation("milestones.milestone", milestone_freezer)
register_freeze_implementation("epics.epic", epic_freezer)
register_freeze_implementation("epics.relateduserstory",
                               epic_related_userstory_freezer)
register_freeze_implementation("userstories.userstory", userstory_freezer)
register_freeze_implementation("issues.issue", issue_freezer)
register_freeze_implementation("tasks.task", task_freezer)
register_freeze_implementation("wiki.wikipage", wikipage_freezer)

register_values_implementation("projects.project", project_values)
register_values_implementation("milestones.milestone", milestone_values)
register_values_implementation("epics.epic", epic_values)
register_values_implementation("epics.relateduserstory",
                               epic_related_userstory_values)
register_values_implementation("userstories.userstory", userstory_values)
register_values_implementation("issues.issue", issue_values)
register_values_implementation("tasks.task", task_values)
register_values_implementation("wiki.wikipage", wikipage_values)
