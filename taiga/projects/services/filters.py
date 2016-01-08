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

from contextlib import closing
from django.db import connection


def _get_project_tags(project):
    result = set()
    tags = project.tags or []
    for tag in tags:
        result.add(tag)
    return result


def _get_stories_tags(project):
    result = set()
    for tags in project.user_stories.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


def _get_tasks_tags(project):
    result = set()
    for tags in project.tasks.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


def _get_issues_tags(project):
    result = set()
    for tags in project.issues.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


# Public api

def get_all_tags(project):
    """
    Given a project, return sorted list of unique
    tags found on it.
    """
    result = set()
    result.update(_get_project_tags(project))
    result.update(_get_issues_tags(project))
    result.update(_get_stories_tags(project))
    result.update(_get_tasks_tags(project))
    return sorted(result)
