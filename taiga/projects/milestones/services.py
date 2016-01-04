# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from . import models



def calculate_milestone_is_closed(milestone):
    return (milestone.user_stories.all().count() > 0 and
            all([task.status.is_closed for task in milestone.tasks.all()]) and
            all([user_story.is_closed for user_story in milestone.user_stories.all()]))


def close_milestone(milestone):
    if not milestone.closed:
        milestone.closed = True
        milestone.save(update_fields=["closed",])


def open_milestone(milestone):
    if milestone.closed:
        milestone.closed = False
        milestone.save(update_fields=["closed",])
