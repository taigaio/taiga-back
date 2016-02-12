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

from contextlib import suppress
from django.core.exceptions import ObjectDoesNotExist
from taiga.projects.history.services import take_snapshot
from taiga.projects.tasks.apps import connect_all_tasks_signals, disconnect_all_tasks_signals


# Enable tasks signals
def enable_tasks_signals(sender, instance, **kwargs):
    connect_all_tasks_signals()


# Disable tasks signals
def disable_task_signals(sender, instance, **kwargs):
    disconnect_all_tasks_signals()

####################################
# Signals for cached prev US
####################################

# Define the previous version of the US for use it on the post_save handler
def cached_prev_us(sender, instance, **kwargs):
    instance.prev = None
    if instance.id:
        instance.prev = sender.objects.get(id=instance.id)


####################################
# Signals of role points
####################################

def update_role_points_when_create_or_edit_us(sender, instance, **kwargs):
    if instance._importing:
        return

    instance.project.update_role_points(user_stories=[instance])


####################################
# Signals for update milestone of tasks
####################################

def update_milestone_of_tasks_when_edit_us(sender, instance, created, **kwargs):
    if not created:
        instance.tasks.update(milestone=instance.milestone)
        for task in instance.tasks.all():
            take_snapshot(task)


####################################
# Signals for close US and Milestone
####################################

def try_to_close_or_open_us_and_milestone_when_create_or_edit_us(sender, instance, created, **kwargs):
    if instance._importing:
        return

    _try_to_close_or_open_us_when_create_or_edit_us(instance)
    _try_to_close_or_open_milestone_when_create_or_edit_us(instance)

def try_to_close_milestone_when_delete_us(sender, instance, **kwargs):
    if instance._importing:
        return

    _try_to_close_milestone_when_delete_us(instance)


# US
def _try_to_close_or_open_us_when_create_or_edit_us(instance):
    if instance._importing:
        return

    from . import services as us_service

    if us_service.calculate_userstory_is_closed(instance):
        us_service.close_userstory(instance)
    else:
        us_service.open_userstory(instance)


# Milestone
def _try_to_close_or_open_milestone_when_create_or_edit_us(instance):
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


def _try_to_close_milestone_when_delete_us(instance):
    if instance._importing:
        return

    from taiga.projects.milestones import services as milestone_service

    with suppress(ObjectDoesNotExist):
        if instance.milestone_id and milestone_service.calculate_milestone_is_closed(instance.milestone):
                milestone_service.close_milestone(instance.milestone)
