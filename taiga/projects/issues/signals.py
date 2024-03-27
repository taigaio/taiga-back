# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from contextlib import suppress
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone


####################################
# Signals for cached prev task
####################################

# Define the previous version of the task for use it on the post_save handler
def cached_prev_issue(sender, instance, **kwargs):
    instance.prev = None
    if instance.id:
        instance.prev = sender.objects.get(id=instance.id)


####################################
# Signals for set finished date
####################################

def set_finished_date_when_edit_issue(sender, instance, **kwargs):
    if instance.status is None:
        return
    if instance.status.is_closed and not instance.finished_date:
        instance.finished_date = timezone.now()
    elif not instance.status.is_closed and instance.finished_date:
        instance.finished_date = None


def try_to_close_or_open_milestone_when_create_or_edit_issue(sender, instance, created, **kwargs):
    if instance._importing:
        return

    _try_to_close_or_open_milestone_when_create_or_edit_issue(instance)


def try_to_close_milestone_when_delete_issue(sender, instance, **kwargs):
    if instance._importing:
        return

    _try_to_close_milestone_when_delete_issue(instance)


# Milestone
def _try_to_close_or_open_milestone_when_create_or_edit_issue(instance):
    if instance._importing:
        return

    from taiga.projects.milestones import services as milestone_service

    if instance.milestone_id:
        if milestone_service.calculate_milestone_is_closed(instance.milestone):
            milestone_service.close_milestone(instance.milestone)
        else:
            milestone_service.open_milestone(instance.milestone)

    if instance.prev and instance.prev.milestone_id and instance.prev.milestone_id != instance.milestone_id:
        if milestone_service.calculate_milestone_is_closed(instance.prev.milestone):
            milestone_service.close_milestone(instance.prev.milestone)
        else:
            milestone_service.open_milestone(instance.prev.milestone)


def _try_to_close_milestone_when_delete_issue(instance):
    if instance._importing:
        return

    from taiga.projects.milestones import services as milestone_service

    with suppress(ObjectDoesNotExist):
        if instance.milestone_id and milestone_service.calculate_milestone_is_closed(instance.milestone):
                milestone_service.close_milestone(instance.milestone)
