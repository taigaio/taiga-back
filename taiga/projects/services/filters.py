# -*- coding: utf-8 -*-
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
