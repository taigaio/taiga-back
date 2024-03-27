# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import connection

from taiga.projects.history import services as history_services
from taiga.projects.history.choices import HistoryType
from taiga.timeline.service import (push_to_timelines,
                                    build_user_namespace,
                                    build_project_namespace,
                                    extract_user_info)


def _push_to_timelines(project, user, obj, event_type, created_datetime, extra_data={}, refresh_totals=True):
    project_id = None if project is None else project.id

    ct = ContentType.objects.get_for_model(obj)
    if settings.CELERY_ENABLED:
        connection.on_commit(lambda: push_to_timelines.delay(project_id,
                                                             user.id,
                                                             ct.app_label,
                                                             ct.model,
                                                             obj.id,
                                                             event_type,
                                                             created_datetime,
                                                             extra_data=extra_data,
                                                             refresh_totals=refresh_totals))
    else:
        push_to_timelines(project_id,
                          user.id,
                          ct.app_label,
                          ct.model,
                          obj.id,
                          event_type,
                          created_datetime,
                          extra_data=extra_data,
                          refresh_totals=refresh_totals)


def _clean_description_fields(values_diff):
    # Description_diff and description_html if included can be huge, we are
    # removing the html one and clearing the diff
    values_diff.pop("description_html", None)
    if "description_diff" in values_diff:
        values_diff["description_diff"] = _("Check the history API for the exact diff")


def on_new_history_entry(sender, instance, created, **kwargs):
    if instance._importing:
        return

    if instance.is_hidden:
        return None

    if instance.user["pk"] is None:
        return None

    refresh_totals = getattr(instance, "refresh_totals", True)

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

    user = get_user_model().objects.get(id=instance.user["pk"])
    values_diff = instance.values_diff
    _clean_description_fields(values_diff)

    extra_data = {
        "values_diff": values_diff,
        "user": extract_user_info(user),
        "comment": instance.comment,
        "comment_html": instance.comment_html,
    }

    # Detect deleted comment
    if instance.delete_comment_date:
        extra_data["comment_deleted"] = True

    # Detect edited comment
    if instance.comment_versions is not None and len(instance.comment_versions)>0:
        extra_data["comment_edited"] = True

    created_datetime = instance.created_at
    _push_to_timelines(project, user, obj, event_type, created_datetime, extra_data=extra_data, refresh_totals=refresh_totals)


def create_membership_push_to_timeline(sender, instance, created, **kwargs):
    """
    Creating new membership with associated user. If the user is the project owner we don't
    do anything because that info will be shown in created project timeline entry

    @param sender: Membership model
    @param instance: Membership object
    """

    # We shown in created project timeline entry
    if created and instance.user and instance.user != instance.project.owner:
        created_datetime = instance.created_at
        _push_to_timelines(instance.project, instance.user, instance, "create", created_datetime)


def delete_membership_push_to_timeline(sender, instance, **kwargs):
    if instance.user:
        created_datetime = timezone.now()
        _push_to_timelines(instance.project, instance.user, instance, "delete", created_datetime)


def create_user_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        project = None
        user = instance
        _push_to_timelines(project, user, user, "create", created_datetime=user.date_joined)
