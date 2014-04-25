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


from django.db.models.loading import get_model


def create_task(id, owner, project, milestone=None, user_story=None, save=True):
    model = get_model("tasks", "Task")

    instance = model(
       subject="Task {0}".format(id),
       description="The Task description.",
       project=project,
       milestone=milestone,
       user_story=user_story,
       status=project.task_statuses.all()[0],
       owner=owner
    )

    if save:
        instance.save()
    return instance
