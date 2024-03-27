# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
    to_tag = to_tag.lower()
    sql = """
        UPDATE userstories_userstory
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE tasks_task
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE issues_issue
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE epics_epic
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);
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
    to_tag = to_tag.lower()
    if update_color:
        color = kwargs.get("color")
    else:
        color = dict(project.tags_colors)[from_tag]
    sql = """
        UPDATE userstories_userstory
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE tasks_task
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE issues_issue
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);

        UPDATE epics_epic
           SET tags = array_distinct(array_replace(tags, %(from_tag)s, %(to_tag)s))
         WHERE project_id = %(project_id)s AND %(from_tag)s = ANY(tags);
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
         WHERE project_id = %(project_id)s AND %(tag)s = ANY(tags);

        UPDATE tasks_task
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s AND %(tag)s = ANY(tags);

        UPDATE issues_issue
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s AND %(tag)s = ANY(tags);

        UPDATE epics_epic
           SET tags = array_remove(tags, %(tag)s)
         WHERE project_id = %(project_id)s AND %(tag)s = ANY(tags);
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
