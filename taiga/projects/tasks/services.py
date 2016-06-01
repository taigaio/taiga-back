# -*- coding: utf-8 -*-
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

import io
import csv

from taiga.base.utils import db, text
from taiga.projects.history.services import take_snapshot
from taiga.projects.tasks.apps import (
    connect_tasks_signals,
    disconnect_tasks_signals)
from taiga.events import events
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset

from . import models


def get_tasks_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of tasks.

    :param bulk_data: List of tasks in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Task` instances.
    """
    return [models.Task(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_tasks_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create tasks from `bulk_data`.

    :param bulk_data: List of tasks in bulk format.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Task` instances.
    """
    tasks = get_tasks_from_bulk(bulk_data, **additional_fields)

    disconnect_tasks_signals()

    try:
        db.save_in_bulk(tasks, callback, precall)
    finally:
        connect_tasks_signals()

    return tasks


def update_tasks_order_in_bulk(bulk_data:list, field:str, project:object):
    """
    Update the order of some tasks.
    `bulk_data` should be a list of tuples with the following format:

    [(<task id>, {<field>: <value>, ...}), ...]
    """
    task_ids = []
    new_order_values = []
    for task_data in bulk_data:
        task_ids.append(task_data["task_id"])
        new_order_values.append({field: task_data["order"]})

    events.emit_event_for_ids(ids=task_ids,
                              content_type="tasks.task",
                              projectid=project.pk)

    db.update_in_bulk_with_ids(task_ids, new_order_values, model=models.Task)


def snapshot_tasks_in_bulk(bulk_data, user):
    task_ids = []
    for task_data in bulk_data:
        try:
            task = models.Task.objects.get(pk=task_data['task_id'])
            take_snapshot(task, user=user)
        except models.Task.DoesNotExist:
            pass


def tasks_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "user_story", "sprint", "sprint_estimated_start",
                  "sprint_estimated_finish", "owner", "owner_full_name", "assigned_to",
                  "assigned_to_full_name", "status", "is_iocaine", "is_closed", "us_order",
                  "taskboard_order", "attachments", "external_reference", "tags", "watchers", "voters",
                  "created_date", "modified_date", "finished_date"]

    custom_attrs = project.taskcustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related("attachments",
                                         "custom_attributes_values")
    queryset = queryset.select_related("milestone",
                                       "owner",
                                       "assigned_to",
                                       "status",
                                       "project")

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for task in queryset:
        task_data = {
            "ref": task.ref,
            "subject": task.subject,
            "description": task.description,
            "user_story": task.user_story.ref if task.user_story else None,
            "sprint": task.milestone.name if task.milestone else None,
            "sprint_estimated_start": task.milestone.estimated_start if task.milestone else None,
            "sprint_estimated_finish": task.milestone.estimated_finish if task.milestone else None,
            "owner": task.owner.username if task.owner else None,
            "owner_full_name": task.owner.get_full_name() if task.owner else None,
            "assigned_to": task.assigned_to.username if task.assigned_to else None,
            "assigned_to_full_name": task.assigned_to.get_full_name() if task.assigned_to else None,
            "status": task.status.name if task.status else None,
            "is_iocaine": task.is_iocaine,
            "is_closed": task.status is not None and task.status.is_closed,
            "us_order": task.us_order,
            "taskboard_order": task.taskboard_order,
            "attachments": task.attachments.count(),
            "external_reference": task.external_reference,
            "tags": ",".join(task.tags or []),
            "watchers": task.watchers,
            "voters": task.total_voters,
            "created_date": task.created_date,
            "modified_date": task.modified_date,
            "finished_date": task.finished_date,            
        }
        for custom_attr in custom_attrs:
            value = task.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            task_data[custom_attr.name] = value

        writer.writerow(task_data)

    return csv_data
