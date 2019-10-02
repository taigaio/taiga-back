import pytest

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

    us_history_change = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test:change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        diff=[],
    )

    take_snapshot(us, user=us.owner)
    return create_notification(project, key, owner, [us_history_change])


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

    epic_history_change = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": owner.id},
        comment="test:change",
        type=HistoryType.change,
        key=key,
        is_hidden=False,
        diff=[],
    )

    take_snapshot(epic, user=epic.owner)
    return create_notification(project, key, owner, [epic_history_change])


@pytest.mark.django_db
def test_sync_send_notifications():
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=["view_issues", "view_us", "view_tasks", "view_wiki_pages"],
    )
    member = f.MembershipFactory.create(project=project, role=role)

    notification = create_us_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert notification.id == sent
    assert 1 == len(entries)

    notification = create_task_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert not sent
    assert not len(entries)

    notification = create_epic_context(project, member.user)
    sent, entries = services.send_sync_notifications(notification.id)
    assert notification.id == sent
    assert 1 == len(entries)
