# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from django.conf import settings

from taiga.projects.services.filters import get_all_tags
from taiga.projects.models import Project

from hashlib import sha1


def _generate_color(tag):
    color = sha1(tag.encode("utf-8")).hexdigest()[0:6]
    return "#{}".format(color)


def _get_new_color(tag, predefined_colors, exclude=[]):
    colors = list(set(predefined_colors) - set(exclude))
    if colors:
        return colors[0]
    return _generate_color(tag)


def remove_unused_tags(project):
    current_tags = get_all_tags(project)
    project.tags_colors = list(filter(lambda x: x[0] in current_tags, project.tags_colors))


def update_project_tags_colors_handler(instance):
    if instance.tags is None:
        instance.tags = []

    if not isinstance(instance.project.tags_colors, list):
        instance.project.tags_colors = []

    for tag in instance.tags:
        defined_tags = map(lambda x: x[0], instance.project.tags_colors)
        if tag not in defined_tags:
            used_colors = map(lambda x: x[1], instance.project.tags_colors)
            new_color = _get_new_color(tag, settings.TAGS_PREDEFINED_COLORS,
                                       exclude=used_colors)
            instance.project.tags_colors.append([tag, new_color])
        
    remove_unused_tags(instance.project)

    if not isinstance(instance, Project):
        instance.project.save()
