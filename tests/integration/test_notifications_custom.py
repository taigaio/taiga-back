# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.conf import settings

from .. import factories as f

from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import make_key_from_model_object, take_snapshot
from taiga.projects.notifications import models
from taiga.projects.notifications import services


def create_notification(
    project, key, owner, history_entries, history_type=HistoryType.change
):
    notification, created = models.HistoryChangeNotification.objects.select_for_update().get_or_create(
        key=key, owner=owner, project=project, history_type=HistoryType.change
    )
    notification.history_entries.add(*history_entries)
    return notification


def create_us_context(project, owner):
    us = f.UserStoryFactory.create(project=project, owner=owner)
    key = make_key_from_model_object(us)

    hc1 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test:change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {}},
        diff={"description": "test:desc"},
    )

    # not notifiable
    hc2 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {}},
        diff={"content": "test:content"},
    )

    hc3 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {"5": "Administrator", "11": "Angela Perez"}},
        diff={"users": {"5": "Administrator", "11": "Angela Perez"}},
    )

    # not notifiable
    hc4 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": [], "status": {"1": "New", "3": "In progress"}},
        diff={"content": "test:content"},
    )

    take_snapshot(us, user=us.owner)
    return create_notification(project, key, owner, [hc1, hc2, hc3, hc4])


def create_task_context(project, owner):
    task = f.TaskFactory(project=project, owner=owner)
    key = make_key_from_model_object(task)

    task_history_change = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test:change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        diff=[],
    )

    take_snapshot(task, user=task.owner)
    return create_notification(project, key, owner, [task_history_change])


def create_epic_context(project, owner):
    epic = f.EpicFactory.create(project=project, owner=owner)
    key = make_key_from_model_object(epic)

    hc1 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.create,
        key=key,
        is_hidden=False,
        diff={"description": "new description"},
    )

    hc2 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test: change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        diff={"content": "change content"},
    )

    hc3 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        diff={"blocked_note": "blocked note"},
    )

    take_snapshot(epic, user=epic.owner)
    return create_notification(project, key, owner, [hc1, hc2, hc3])


def create_issue_context(project, owner):
    issue = f.IssueFactory.create(project=project, owner=owner)
    key = make_key_from_model_object(issue)

    hc1 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test:change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {}},
        diff={"description": "test:desc"},
    )

    # not notifiable
    hc2 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {}},
        diff={"content": "test:content"},
    )

    hc3 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": {"5": "Administrator", "11": "Angela Perez"}},
        diff={"users": {"5": "Administrator", "11": "Angela Perez"}},
    )

    # not notifiable
    hc4 = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        values={"users": [], "status": {"1": "New", "3": "In progress"}},
        diff={"content": "test:content"},
    )

    take_snapshot(issue, user=issue.owner)
    return create_notification(project, key, owner, [hc1, hc2, hc3, hc4])


@pytest.mark.django_db
def test_sync_send_notifications():
    settings.NOTIFICATIONS_CUSTOM_FILTER = True
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=["view_issues", "view_us", "view_tasks", "view_wiki_pages"],
    )
    member = f.MembershipFactory.create(project=project, role=role)

    notification = create_epic_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert notification.id == sent
    assert 2 == len(entries)

    notification = create_us_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert notification.id == sent
    assert 2 == len(entries)

    notification = create_issue_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert notification.id == sent
    assert 2 == len(entries)

    notification = create_task_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert not sent
    assert not len(entries)

    # restore settings
    settings.NOTIFICATIONS_CUSTOM_FILTER = False
