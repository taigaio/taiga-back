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
from django.utils import timezone

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


def _push_to_timelines(project, user, obj, event_type, created_datetime, extra_data={}):
    if project is not None:
    # Project timeline
        _push_to_timeline(project, obj, event_type, created_datetime,
            namespace=build_project_namespace(project),
            extra_data=extra_data)

    # User timeline
    _push_to_timeline(user, obj, event_type, created_datetime,
        namespace=build_user_namespace(user),
        extra_data=extra_data)

    # Calculating related people
    related_people = User.objects.none()

    # Assigned to
    if hasattr(obj, "assigned_to") and obj.assigned_to and user != obj.assigned_to:
        related_people |= User.objects.filter(id=obj.assigned_to.id)

    # Watchers
    watchers = hasattr(obj, "watchers") and obj.watchers.exclude(id=user.id) or User.objects.none()
    if watchers:
        related_people |= watchers

    if project is not None:
        # Team
        team_members_ids = project.memberships.filter(user__isnull=False).values_list("id", flat=True)
        team = User.objects.filter(id__in=team_members_ids)
        related_people |= team
        related_people = related_people.distinct()

        _push_to_timeline(related_people, obj, event_type, created_datetime,
            namespace=build_user_namespace(user),
            extra_data=extra_data)

        #Related people: team members


def on_new_history_entry(sender, instance, created, **kwargs):
    if instance._importing:
        return

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
        "comment_html": instance.comment_html,
    }

    # Detect deleted comment
    if instance.delete_comment_date:
        extra_data["comment_deleted"] = True

    created_datetime = instance.created_at
    _push_to_timelines(project, user, obj, event_type, created_datetime, extra_data=extra_data)


def create_membership_push_to_timeline(sender, instance, **kwargs):
    # Creating new membership with associated user
    # If the user is the project owner we don't do anything because that info will
    # be shown in created project timeline entry
    if not instance.pk and instance.user and instance.user != instance.project.owner:
        created_datetime = instance.created_at
        _push_to_timelines(instance.project, instance.user, instance, "create", created_datetime)

    #Updating existing membership
    elif instance.pk:
        prev_instance = sender.objects.get(pk=instance.pk)
        if instance.user != prev_instance.user:
            created_datetime = timezone.now()
            # The new member
            _push_to_timelines(instance.project, instance.user, instance, "create", created_datetime)
            # If we are updating the old user is removed from project
            if prev_instance.user:
                _push_to_timelines(instance.project, prev_instance.user, prev_instance, "delete", created_datetime)


def delete_membership_push_to_timeline(sender, instance, **kwargs):
    if instance.user:
        created_datetime = timezone.now()
        _push_to_timelines(instance.project, instance.user, instance, "delete", created_datetime)


def create_user_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        project = None
        user = instance
        _push_to_timelines(project, user, user, "create", created_datetime=user.date_joined)
