# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.utils import db
from taiga.events import events
from taiga.projects.history.services import take_snapshot
from taiga.projects.services import apply_order_updates
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory


def calculate_milestone_is_closed(milestone):
    all_us_closed = all([user_story.is_closed for user_story in
                         milestone.user_stories.all()])
    all_tasks_closed = all([task.status is not None and task.status.is_closed for task in
                            milestone.tasks.filter(user_story__isnull=True)])
    all_issues_closed = all([issue.is_closed for issue in
                             milestone.issues.all()])

    uss_check = (milestone.user_stories.all().count() > 0
        and all_tasks_closed and all_us_closed and all_issues_closed)
    tasks_check = (milestone.tasks.filter(user_story__isnull=True).count() > 0
        and all_tasks_closed and all_issues_closed and all_us_closed)
    issues_check = (milestone.issues.all().count() > 0
        and all_issues_closed and all_tasks_closed and all_us_closed)

    return uss_check or issues_check or tasks_check


def close_milestone(milestone):
    if not milestone.closed:
        milestone.closed = True
        milestone.save(update_fields=["closed",])

def open_milestone(milestone):
    if milestone.closed:
        milestone.closed = False
        milestone.save(update_fields=["closed",])


def update_userstories_milestone_in_bulk(bulk_data: list, milestone: object):
    """
    Update the milestone and the milestone order of some user stories adding
    the extra orders needed to keep consistency.
    `bulk_data` should be a list of dicts with the following format:
    [{'us_id': <value>, 'order': <value>}, ...]
    """
    user_stories = milestone.user_stories.all()
    us_orders = {us.id: getattr(us, "sprint_order") for us in user_stories}
    new_us_orders = {}
    for e in bulk_data:
        new_us_orders[e["us_id"]] = e["order"]
        # The base orders where we apply the new orders must containg all
        # the values
        us_orders[e["us_id"]] = e["order"]

    apply_order_updates(us_orders, new_us_orders)

    us_milestones = {e["us_id"]: milestone.id for e in bulk_data}
    user_story_ids = us_milestones.keys()

    events.emit_event_for_ids(ids=user_story_ids,
                              content_type="userstories.userstory",
                              projectid=milestone.project.pk)

    us_instance_list = []
    us_values = []
    for us_id in user_story_ids:
        us = UserStory.objects.get(pk=us_id)
        us_instance_list.append(us)
        us_values.append({'milestone_id': milestone.id})

    db.update_in_bulk(us_instance_list, us_values)
    db.update_attr_in_bulk_for_ids(us_orders, "sprint_order", UserStory)

    # Updating the milestone for the tasks
    Task.objects.filter(
        user_story_id__in=[e["us_id"] for e in bulk_data]).update(
        milestone=milestone)

    return us_orders


def snapshot_userstories_in_bulk(bulk_data, user):
    for us_data in bulk_data:
        try:
            us = UserStory.objects.get(pk=us_data['us_id'])
            take_snapshot(us, user=user)
        except UserStory.DoesNotExist:
            pass


def update_tasks_milestone_in_bulk(bulk_data: list, milestone: object):
    """
    Update the milestone and the milestone order of some tasks adding
    the extra orders needed to keep consistency.
    `bulk_data` should be a list of dicts with the following format:
    [{'task_id': <value>, 'order': <value>}, ...]
    """
    tasks = milestone.tasks.all()
    task_orders = {task.id: getattr(task, "taskboard_order") for task in tasks}
    new_task_orders = {}
    for e in bulk_data:
        new_task_orders[e["task_id"]] = e["order"]
        # The base orders where we apply the new orders must containg all
        # the values
        task_orders[e["task_id"]] = e["order"]

    apply_order_updates(task_orders, new_task_orders)

    task_milestones = {e["task_id"]: milestone.id for e in bulk_data}
    task_ids = task_milestones.keys()

    events.emit_event_for_ids(ids=task_ids,
                              content_type="tasks.task",
                              projectid=milestone.project.pk)


    task_instance_list = []
    task_values = []
    for task_id in task_ids:
        task = Task.objects.get(pk=task_id)
        task_instance_list.append(task)
        task_values.append({'milestone_id': milestone.id})

    db.update_in_bulk(task_instance_list, task_values)
    db.update_attr_in_bulk_for_ids(task_orders, "taskboard_order", Task)

    return task_milestones


def snapshot_tasks_in_bulk(bulk_data, user):
    for task_data in bulk_data:
        try:
            task = Task.objects.get(pk=task_data['task_id'])
            take_snapshot(task, user=user)
        except Task.DoesNotExist:
            pass


def update_issues_milestone_in_bulk(bulk_data: list, milestone: object):
    """
    Update the milestone some issues adding
    `bulk_data` should be a list of dicts with the following format:
    [{'task_id': <value>}, ...]
    """
    issue_milestones = {e["issue_id"]: milestone.id for e in bulk_data}
    issue_ids = issue_milestones.keys()

    events.emit_event_for_ids(ids=issue_ids,
                              content_type="issues.issues",
                              projectid=milestone.project.pk)

    issues_instance_list = []
    issues_values = []
    for issue_id in issue_ids:
        issue = Issue.objects.get(pk=issue_id)
        issues_instance_list.append(issue)
        issues_values.append({'milestone_id': milestone.id})

    db.update_in_bulk(issues_instance_list, issues_values)

    return issue_milestones


def snapshot_issues_in_bulk(bulk_data, user):
    for issue_data in bulk_data:
        try:
            issue = Issue.objects.get(pk=issue_data['issue_id'])
            take_snapshot(issue, user=user)
        except Issue.DoesNotExist:
            pass
