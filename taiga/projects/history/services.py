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
from functools import lru_cache

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, InvalidPage
from django.db.models.loading import get_model
from django.db import transaction as tx

from taiga.mdrender.service import render as mdrender
from taiga.mdrender.service import get_diff_of_htmls
from taiga.base.utils.db import get_typename_for_model_class

from .models import HistoryType


# Type that represents a freezed object
FrozenObj = namedtuple("FrozenObj", ["key", "snapshot"])
FrozenDiff = namedtuple("FrozenDiff", ["key", "diff", "snapshot"])

# Dict containing registred contentypes with their freeze implementation.
_freeze_impl_map = {}

# Dict containing registred containing with their values implementation.
_values_impl_map = {}

log = logging.getLogger("taiga.history")


def make_key_from_model_object(obj:object) -> str:
    """
    Create unique key from model instance.
    """
    tn = get_typename_for_model_class(obj.__class__)
    return "{0}:{1}".format(tn, obj.pk)


def register_values_implementation(typename:str, fn=None):
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


def register_freeze_implementation(typename:str, fn=None):
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

def freeze_model_instance(obj:object) -> FrozenObj:
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
    return FrozenObj(key, impl_fn(obj))


def make_diff(oldobj:FrozenObj, newobj:FrozenObj) -> FrozenDiff:
    """
    Compute a diff between two frozen objects.
    """

    assert isinstance(newobj, FrozenObj), "newobj parameter should be instance of FrozenObj"

    if oldobj is None:
        return FrozenDiff(newobj.key, {}, newobj.snapshot)

    first = oldobj.snapshot
    second = newobj.snapshot

    diff = {}
    not_found_value = None

    # Check all keys in first dict
    for key in first:
        if key not in second:
            diff[key] = (first[key], not_found_value)
        elif first[key] != second[key]:
            diff[key] = (first[key], second[key])

    # Check all keys in second dict to find missing
    for key in second:
        if key not in first:
            diff[key] = (not_found_value, second[key])

    if "description" in diff:
        description_diff = get_diff_of_htmls(
            diff["description"][0],
            diff["description"][1]
        )
        diff["description_diff"] = (not_found_value, description_diff)

    return FrozenDiff(newobj.key, diff, newobj.snapshot)


def make_diff_values(typename:str, fdiff:FrozenDiff) -> dict:
    """
    Given a typename and diff, build a values dict for it.
    If no implementation found for typename, warnig is raised in
    logging and returns empty dict.
    """

    if typename not in _values_impl_map:
        log.warning("No implementation found of '{}' for values.".format(typename))
        return {}

    impl_fn = _values_impl_map[typename]
    return impl_fn(fdiff.diff)


def _rebuild_snapshot_from_diffs(keysnapshot, partials):
    result = deepcopy(keysnapshot)

    for part in partials:
        for key, value in part.diff.items():
            result[key] = value[1]

    return result


def get_last_snapshot_for_key(key:str) -> FrozenObj:
    entry_model = get_model("history", "HistoryEntry")

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

@tx.atomic
def take_snapshot(obj:object, *, comment:str="", user=None, delete:bool=False):
    """
    Given any model instance with registred content type,
    create new history entry of "change" type.

    This raises exception in case of object wasn't
    previously freezed.
    """

    key = make_key_from_model_object(obj)
    typename = get_typename_for_model_class(obj.__class__)

    new_fobj = freeze_model_instance(obj)
    old_fobj, need_real_snapshot = get_last_snapshot_for_key(key)

    entry_model = get_model("history", "HistoryEntry")
    user_id = None if user is None else user.id
    user_name = "" if user is None else user.get_full_name()

    # Determine history type
    if delete:
        entry_type = HistoryType.delete
    elif new_fobj and not old_fobj:
        entry_type = HistoryType.create
    elif new_fobj and old_fobj:
        entry_type = HistoryType.change
    else:
        raise RuntimeError("Unexpected condition")

    kwargs = {
        "user": {"pk": user_id, "name": user_name},
        "key": key,
        "type": entry_type,
        "comment": "",
        "comment_html": "",
        "diff": None,
        "values": None,
        "snapshot": None,
        "is_snapshot": False,
    }

    fdiff = make_diff(old_fobj, new_fobj)
    fvals = make_diff_values(typename, fdiff)

    # If diff and comment are empty, do
    # not create empty history entry
    if (not fdiff.diff and not comment
        and old_fobj is not None
        and entry_type != HistoryType.delete):

        return None

    kwargs.update({
        "snapshot": fdiff.snapshot if need_real_snapshot else None,
        "is_snapshot": need_real_snapshot,
        "values": fvals,
        "comment": comment,
        "diff": fdiff.diff,
        "comment_html": mdrender(obj.project, comment),
    })

    return entry_model.objects.create(**kwargs)


# High level query api

def get_history_queryset_by_model_instance(obj:object, types=(HistoryType.change,)):
    """
    Get one page of history for specified object.
    """
    key = make_key_from_model_object(obj)
    history_entry_model = get_model("history", "HistoryEntry")

    qs = history_entry_model.objects.filter(key=key, type__in=types)
    return qs.order_by("-created_at")


# Freeze implementatitions
from .freeze_impl import project_freezer
from .freeze_impl import milestone_freezer
from .freeze_impl import userstory_freezer
from .freeze_impl import issue_freezer
from .freeze_impl import task_freezer
from .freeze_impl import wikipage_freezer

register_freeze_implementation("projects.project", project_freezer)
register_freeze_implementation("milestones.milestone", milestone_freezer,)
register_freeze_implementation("userstories.userstory", userstory_freezer)
register_freeze_implementation("issues.issue", issue_freezer)
register_freeze_implementation("tasks.task", task_freezer)
register_freeze_implementation("wiki.wikipage", wikipage_freezer)

from .freeze_impl import milestone_values
from .freeze_impl import userstory_values
from .freeze_impl import issue_values
from .freeze_impl import task_values
from .freeze_impl import wikipage_values

register_values_implementation("milestones.milestone", milestone_values)
register_values_implementation("userstories.userstory", userstory_values)
register_values_implementation("issues.issue", issue_values)
register_values_implementation("tasks.task", task_values)
register_values_implementation("wiki.wikipage", wikipage_values)
