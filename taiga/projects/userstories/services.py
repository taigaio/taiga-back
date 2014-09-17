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

from django.utils import timezone

from taiga.base.utils import db, text
from taiga.projects.history.services import take_snapshot
from taiga.events import events

from . import models


def get_userstories_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of user stories.

    :param bulk_data: List of user stories in bulk format.
    :param additional_fields: Additional fields when instantiating each user story.

    :return: List of `UserStory` instances.
    """
    return [models.UserStory(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_userstories_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create user stories from `bulk_data`.

    :param bulk_data: List of user stories in bulk format.
    :param callback: Callback to execute after each user story save.
    :param additional_fields: Additional fields when instantiating each user story.

    :return: List of created `Task` instances.
    """
    userstories = get_userstories_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(userstories, callback, precall)
    return userstories


def update_userstories_order_in_bulk(bulk_data:list, field:str, project:object):
    """
    Update the order of some user stories.
    `bulk_data` should be a list of tuples with the following format:

    [(<user story id>, {<field>: <value>, ...}), ...]
    """
    user_story_ids = []
    new_order_values = []
    for us_data in bulk_data:
        user_story_ids.append(us_data["us_id"])
        new_order_values.append({field: us_data["order"]})

    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=project.pk)

    db.update_in_bulk_with_ids(user_story_ids, new_order_values, model=models.UserStory)


def snapshot_userstories_in_bulk(bulk_data, user):
    user_story_ids = []
    for us_data in bulk_data:
        try:
            us = models.UserStory.objects.get(pk=us_data['us_id'])
            take_snapshot(us, user=user)
        except models.UserStory.DoesNotExist:
            pass


def calculate_userstory_is_closed(user_story):
    if user_story.status is None:
        return False

    if user_story.tasks.count() == 0:
        return user_story.status.is_closed

    if all([task.status.is_closed for task in user_story.tasks.all()]):
        return True

    return False


def close_userstory(us):
    if not us.is_closed:
        us.is_closed = True
        us.finish_date = timezone.now()
        us.save(update_fields=["is_closed", "finish_date"])


def open_userstory(us):
    if us.is_closed:
        us.is_closed = False
        us.finish_date = None
        us.save(update_fields=["is_closed", "finish_date"])
