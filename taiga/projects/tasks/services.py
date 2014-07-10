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

from taiga.base.utils import db, text

from . import models


def get_tasks_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of tasks.

    :param bulk_data: List of tasks in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Task` instances.
    """
    return [models.Task(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_tasks_in_bulk(bulk_data, callback=None, **additional_fields):
    """Create tasks from `bulk_data`.

    :param bulk_data: List of tasks in bulk format.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Task` instances.
    """
    tasks = get_tasks_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(tasks, callback)
    return tasks
