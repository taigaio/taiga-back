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

from django.db import transaction
from django.db import connection

from . import models


class TasksService(object):
    @transaction.atomic
    def bulk_insert(self, project, user, user_story, data, callback_on_success=None):
        tasks = []

        items = filter(lambda s: len(s) > 0,
                    map(lambda s: s.strip(), data.split("\n")))

        for item in items:
            obj = models.Task.objects.create(subject=item, project=project,
                                             user_story=user_story, owner=user,
                                             status=project.default_task_status)
            tasks.append(obj)

            if callback_on_success:
                callback_on_success(obj, True)

        return tasks

