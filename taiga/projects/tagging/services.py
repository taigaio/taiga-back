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

from django.db import connection


def tag_exist_for_project_elements(project, tag):
    return tag in dict(project.tags_colors).keys()


def create_tags(project, new_tags_colors):
    project.tags_colors += [[k.lower(), v] for k, v in new_tags_colors.items()]
    project.save(update_fields=["tags_colors"])


def create_tag(project, tag, color):
    project.tags_colors.append([tag.lower(), color])
    project.save(update_fields=["tags_colors"])


def edit_tag(project, from_tag, to_tag, color):
    sql = """
        UPDATE userstories_userstory
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE tasks_task
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE issues_issue
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE epics_epic
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;
    """
    cursor = connection.cursor()
    cursor.execute(sql, params={"from_tag": from_tag, "to_tag": to_tag, "project_id": project.id})

    tags_colors = dict(project.tags_colors)
    tags_colors.pop(from_tag)
    tags_colors[to_tag] = color
    project.tags_colors = list(tags_colors.items())
    project.save(update_fields=["tags_colors"])


def rename_tag(project, from_tag, to_tag, **kwargs):
    # Kwargs can have a color parameter
    update_color = "color" in kwargs
    if update_color:
        color = kwargs.get("color")
    else:
        color = dict(project.tags_colors)[from_tag]
    sql = """
        UPDATE userstories_userstory
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE tasks_task
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE issues_issue
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;

        UPDATE epics_epic
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s;
    """
    cursor = connection.cursor()
    cursor.execute(sql, params={"from_tag": from_tag, "to_tag": to_tag, "project_id": project.id})

    tags_colors = dict(project.tags_colors)
    tags_colors.pop(from_tag)
    tags_colors[to_tag] = color
    project.tags_colors = list(tags_colors.items())
    project.save(update_fields=["tags_colors"])


def delete_tag(project, tag):
    sql = """
        UPDATE userstories_userstory
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s;

        UPDATE tasks_task
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s;

        UPDATE issues_issue
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s;

        UPDATE epics_epic
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s;
    """
    cursor = connection.cursor()
    cursor.execute(sql, params={"tag": tag, "project_id": project.id})

    tags_colors = dict(project.tags_colors)
    del tags_colors[tag]
    project.tags_colors = list(tags_colors.items())
    project.save(update_fields=["tags_colors"])


def mix_tags(project, from_tags, to_tag):
    color = dict(project.tags_colors)[to_tag]
    for from_tag in from_tags:
        rename_tag(project, from_tag, to_tag, color=color)
