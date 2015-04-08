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

from django.conf import settings

from taiga.projects.history import services as history_services
from taiga.projects.models import Project
from taiga.users.models import User
from taiga.projects.history.choices import HistoryType
from taiga.timeline.service import (push_to_timeline, build_user_namespace,
    build_project_namespace, extract_user_info)

# TODO: Add events to followers timeline when followers are implemented.
# TODO: Add events to project watchers timeline when project watchers are implemented.

def _push_to_timeline(*args, **kwargs):
    if settings.CELERY_ENABLED:
        push_to_timeline.delay(*args, **kwargs)
    else:
        push_to_timeline(*args, **kwargs)


def _push_to_timelines(project, user, obj, event_type, extra_data={}):
    # Project timeline
    _push_to_timeline(project, obj, event_type,
        namespace=build_project_namespace(project),
        extra_data=extra_data)

    # User timeline
    _push_to_timeline(user, obj, event_type,
        namespace=build_user_namespace(user),
        extra_data=extra_data)

    # Related people: watchers and assigned to
    if hasattr(obj, "assigned_to") and obj.assigned_to and user != obj.assigned_to:
        _push_to_timeline(obj.assigned_to, obj, event_type,
            namespace=build_user_namespace(user),
            extra_data=extra_data)

    watchers = hasattr(obj, "watchers") and obj.watchers.exclude(id=user.id) or []
    if watchers:
        _push_to_timeline(watchers, obj, event_type,
            namespace=build_user_namespace(user),
            extra_data=extra_data)


def on_new_history_entry(sender, instance, created, **kwargs):
    if instance.is_hidden:
        return None

    model = history_services.get_model_from_key(instance.key)
    pk = history_services.get_pk_from_key(instance.key)
    obj = model.objects.get(pk=pk)
    project = obj.project

    if instance.type == HistoryType.create:
        event_type = "create"
    elif instance.type == HistoryType.change:
        event_type = "change"
    elif instance.type == HistoryType.delete:
        event_type = "delete"

    user = User.objects.get(id=instance.user["pk"])

    extra_data = {
        "values_diff": instance.values_diff,
        "user": extract_user_info(user),
        "comment": instance.comment,
    }

    _push_to_timelines(project, user, obj, event_type, extra_data=extra_data)


def create_membership_push_to_timeline(sender, instance, **kwargs):
    # Creating new membership with associated user
    if not instance.pk and instance.user:
        _push_to_timelines(instance.project, instance.user, instance, "create")

    #Updating existing membership
    elif instance.pk:
        prev_instance = sender.objects.get(pk=instance.pk)
        if instance.user != prev_instance.user:
            # The new member
            _push_to_timelines(instance.project, instance.user, instance, "create")
            # If we are updating the old user is removed from project
            if prev_instance.user:
                _push_to_timelines(instance.project, prev_instance.user, prev_instance, "delete")


def delete_membership_push_to_timeline(sender, instance, **kwargs):
    if instance.user:
        _push_to_timelines(instance.project, instance.user, instance, "delete")
