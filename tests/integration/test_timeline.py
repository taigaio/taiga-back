# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from datetime import timedelta
import pytest

from .. import factories
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from taiga.timeline.service import build_project_namespace, build_user_namespace, get_timeline
from taiga.projects.history import services as history_services
from taiga.timeline import service
from taiga.timeline.models import Timeline
from taiga.timeline.serializers import TimelineSerializer


pytestmark = pytest.mark.django_db


def test_add_to_object_timeline():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    task = factories.TaskFactory()

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))

    service._add_to_object_timeline(user1, task, "test", task.created_date)

    assert Timeline.objects.filter(object_id=user1.id).count() == 2
    assert Timeline.objects.order_by("-id")[0].data == id(task)


def test_get_timeline():
    Timeline.objects.all().delete()

    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    user3 = factories.UserFactory()
    task1= factories.TaskFactory()
    task2= factories.TaskFactory()
    task3= factories.TaskFactory()
    task4= factories.TaskFactory()

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))

    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    service._add_to_object_timeline(user1, task3, "test", task3.created_date)
    service._add_to_object_timeline(user1, task4, "test", task4.created_date)
    service._add_to_object_timeline(user2, task1, "test", task1.created_date)

    assert Timeline.objects.filter(object_id=user1.id).count() == 5
    assert Timeline.objects.filter(object_id=user2.id).count() == 2
    assert Timeline.objects.filter(object_id=user3.id).count() == 1


def test_filter_timeline_no_privileges():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    task1= factories.TaskFactory()

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 0


def test_filter_timeline_public_project():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    project = factories.ProjectFactory.create(is_private=False)
    task1= factories.TaskFactory()
    task2= factories.TaskFactory.create(project=project)

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 1


def test_filter_timeline_private_project_anon_permissions():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    project = factories.ProjectFactory.create(is_private=True, anon_permissions= ["view_tasks"])
    task1= factories.TaskFactory()
    task2= factories.TaskFactory.create(project=project)

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 1


def test_filter_timeline_private_project_member_permissions():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    project = factories.ProjectFactory.create(is_private=True)
    membership = factories.MembershipFactory.create(user=user2, project=project)
    membership.role.permissions = ["view_tasks"]
    membership.role.save()
    task1= factories.TaskFactory()
    task2= factories.TaskFactory.create(project=project)

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 3


def test_filter_timeline_private_project_member_admin():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    project = factories.ProjectFactory.create(is_private=True)
    membership = factories.MembershipFactory.create(user=user2, project=project, is_admin=True)
    task1= factories.TaskFactory()
    task2= factories.TaskFactory.create(project=project)

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 3


def test_filter_timeline_private_project_member_superuser():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory(is_superuser=True)
    project = factories.ProjectFactory.create(is_private=True)

    task1= factories.TaskFactory()
    task2= factories.TaskFactory.create(project=project)

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: id(x))
    service._add_to_object_timeline(user1, task1, "test", task1.created_date)
    service._add_to_object_timeline(user1, task2, "test", task2.created_date)
    timeline = Timeline.objects.exclude(event_type="users.user.create")
    timeline = service.filter_timeline_for_user(timeline, user2)
    assert timeline.count() == 2


def test_create_project_timeline():
    project = factories.ProjectFactory.create(name="test project timeline")
    history_services.take_snapshot(project, user=project.owner)
    project_timeline = service.get_project_timeline(project)
    assert project_timeline[0].event_type == "projects.project.create"
    assert project_timeline[0].data["project"]["name"] == "test project timeline"
    assert project_timeline[0].data["user"]["id"] == project.owner.id


def test_create_milestone_timeline():
    milestone = factories.MilestoneFactory.create(name="test milestone timeline")
    history_services.take_snapshot(milestone, user=milestone.owner)
    milestone_timeline = service.get_project_timeline(milestone.project)
    assert milestone_timeline[0].event_type == "milestones.milestone.create"
    assert milestone_timeline[0].data["milestone"]["name"] == "test milestone timeline"
    assert milestone_timeline[0].data["user"]["id"] == milestone.owner.id


def test_create_user_story_timeline():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    project_timeline = service.get_project_timeline(user_story.project)
    assert project_timeline[0].event_type == "userstories.userstory.create"
    assert project_timeline[0].data["userstory"]["subject"] == "test us timeline"
    assert project_timeline[0].data["user"]["id"] == user_story.owner.id


def test_create_issue_timeline():
    issue = factories.IssueFactory.create(subject="test issue timeline")
    history_services.take_snapshot(issue, user=issue.owner)
    project_timeline = service.get_project_timeline(issue.project)
    assert project_timeline[0].event_type == "issues.issue.create"
    assert project_timeline[0].data["issue"]["subject"] == "test issue timeline"
    assert project_timeline[0].data["user"]["id"] == issue.owner.id


def test_create_task_timeline():
    task = factories.TaskFactory.create(subject="test task timeline")
    history_services.take_snapshot(task, user=task.owner)
    project_timeline = service.get_project_timeline(task.project)
    assert project_timeline[0].event_type == "tasks.task.create"
    assert project_timeline[0].data["task"]["subject"] == "test task timeline"
    assert project_timeline[0].data["user"]["id"] == task.owner.id


def test_create_wiki_page_timeline():
    page = factories.WikiPageFactory.create(slug="test wiki page timeline")
    history_services.take_snapshot(page, user=page.owner)
    project_timeline = service.get_project_timeline(page.project)
    assert project_timeline[0].event_type == "wiki.wikipage.create"
    assert project_timeline[0].data["wikipage"]["slug"] == "test wiki page timeline"
    assert project_timeline[0].data["user"]["id"] == page.owner.id


def test_create_membership_timeline():
    membership = factories.MembershipFactory.create()
    project_timeline = service.get_project_timeline(membership.project)
    user_timeline = service.get_user_timeline(membership.user)
    assert project_timeline[0].event_type == "projects.membership.create"
    assert project_timeline[0].data["project"]["id"] == membership.project.id
    assert project_timeline[0].data["user"]["id"] == membership.user.id
    assert user_timeline[0].event_type == "projects.membership.create"
    assert user_timeline[0].data["project"]["id"] == membership.project.id
    assert user_timeline[0].data["user"]["id"] == membership.user.id


def test_update_project_timeline():
    user_watcher= factories.UserFactory()
    project = factories.ProjectFactory.create(name="test project timeline")
    history_services.take_snapshot(project, user=project.owner)
    project.add_watcher(user_watcher)
    project.name = "test project timeline updated"
    project.save()
    history_services.take_snapshot(project, user=project.owner)
    project_timeline = service.get_project_timeline(project)
    assert project_timeline[0].event_type == "projects.project.change"
    assert project_timeline[0].data["project"]["name"] == "test project timeline updated"
    assert project_timeline[0].data["values_diff"]["name"][0] == "test project timeline"
    assert project_timeline[0].data["values_diff"]["name"][1] == "test project timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "projects.project.change"
    assert user_watcher_timeline[0].data["project"]["name"] == "test project timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["name"][0] == "test project timeline"
    assert user_watcher_timeline[0].data["values_diff"]["name"][1] == "test project timeline updated"


def test_update_milestone_timeline():
    user_watcher= factories.UserFactory()
    milestone = factories.MilestoneFactory.create(name="test milestone timeline")
    history_services.take_snapshot(milestone, user=milestone.owner)
    milestone.add_watcher(user_watcher)
    milestone.name = "test milestone timeline updated"
    milestone.save()
    history_services.take_snapshot(milestone, user=milestone.owner)
    project_timeline = service.get_project_timeline(milestone.project)
    assert project_timeline[0].event_type == "milestones.milestone.change"
    assert project_timeline[0].data["milestone"]["name"] == "test milestone timeline updated"
    assert project_timeline[0].data["values_diff"]["name"][0] == "test milestone timeline"
    assert project_timeline[0].data["values_diff"]["name"][1] == "test milestone timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "milestones.milestone.change"
    assert user_watcher_timeline[0].data["milestone"]["name"] == "test milestone timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["name"][0] == "test milestone timeline"
    assert user_watcher_timeline[0].data["values_diff"]["name"][1] == "test milestone timeline updated"


def test_update_user_story_timeline():
    user_watcher= factories.UserFactory()
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_story.add_watcher(user_watcher)
    user_story.subject = "test us timeline updated"
    user_story.save()
    history_services.take_snapshot(user_story, user=user_story.owner)
    project_timeline = service.get_project_timeline(user_story.project)
    assert project_timeline[0].event_type == "userstories.userstory.change"
    assert project_timeline[0].data["userstory"]["subject"] == "test us timeline updated"
    assert project_timeline[0].data["values_diff"]["subject"][0] == "test us timeline"
    assert project_timeline[0].data["values_diff"]["subject"][1] == "test us timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "userstories.userstory.change"
    assert user_watcher_timeline[0].data["userstory"]["subject"] == "test us timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][0] == "test us timeline"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][1] == "test us timeline updated"


def test_update_issue_timeline():
    user_watcher= factories.UserFactory()
    issue = factories.IssueFactory.create(subject="test issue timeline")
    history_services.take_snapshot(issue, user=issue.owner)
    issue.add_watcher(user_watcher)
    issue.subject = "test issue timeline updated"
    issue.save()
    history_services.take_snapshot(issue, user=issue.owner)
    project_timeline = service.get_project_timeline(issue.project)
    assert project_timeline[0].event_type == "issues.issue.change"
    assert project_timeline[0].data["issue"]["subject"] == "test issue timeline updated"
    assert project_timeline[0].data["values_diff"]["subject"][0] == "test issue timeline"
    assert project_timeline[0].data["values_diff"]["subject"][1] == "test issue timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "issues.issue.change"
    assert user_watcher_timeline[0].data["issue"]["subject"] == "test issue timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][0] == "test issue timeline"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][1] == "test issue timeline updated"


def test_update_task_timeline():
    user_watcher= factories.UserFactory()
    task = factories.TaskFactory.create(subject="test task timeline")
    history_services.take_snapshot(task, user=task.owner)
    task.add_watcher(user_watcher)
    task.subject = "test task timeline updated"
    task.save()
    history_services.take_snapshot(task, user=task.owner)
    project_timeline = service.get_project_timeline(task.project)
    assert project_timeline[0].event_type == "tasks.task.change"
    assert project_timeline[0].data["task"]["subject"] == "test task timeline updated"
    assert project_timeline[0].data["values_diff"]["subject"][0] == "test task timeline"
    assert project_timeline[0].data["values_diff"]["subject"][1] == "test task timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "tasks.task.change"
    assert user_watcher_timeline[0].data["task"]["subject"] == "test task timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][0] == "test task timeline"
    assert user_watcher_timeline[0].data["values_diff"]["subject"][1] == "test task timeline updated"


def test_update_wiki_page_timeline():
    user_watcher= factories.UserFactory()
    page = factories.WikiPageFactory.create(slug="test wiki page timeline")
    history_services.take_snapshot(page, user=page.owner)
    page.add_watcher(user_watcher)
    page.slug = "test wiki page timeline updated"
    page.save()
    history_services.take_snapshot(page, user=page.owner)
    project_timeline = service.get_project_timeline(page.project)
    assert project_timeline[0].event_type == "wiki.wikipage.change"
    assert project_timeline[0].data["wikipage"]["slug"] == "test wiki page timeline updated"
    assert project_timeline[0].data["values_diff"]["slug"][0] == "test wiki page timeline"
    assert project_timeline[0].data["values_diff"]["slug"][1] == "test wiki page timeline updated"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "wiki.wikipage.change"
    assert user_watcher_timeline[0].data["wikipage"]["slug"] == "test wiki page timeline updated"
    assert user_watcher_timeline[0].data["values_diff"]["slug"][0] == "test wiki page timeline"
    assert user_watcher_timeline[0].data["values_diff"]["slug"][1] == "test wiki page timeline updated"


def test_delete_project_timeline():
    project = factories.ProjectFactory.create(name="test project timeline")
    user_watcher= factories.UserFactory()
    project.add_watcher(user_watcher)
    history_services.take_snapshot(project, user=project.owner, delete=True)
    user_timeline = service.get_project_timeline(project)
    assert user_timeline[0].event_type == "projects.project.delete"
    assert user_timeline[0].data["project"]["id"] == project.id
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "projects.project.delete"
    assert user_watcher_timeline[0].data["project"]["id"] == project.id


def test_delete_milestone_timeline():
    milestone = factories.MilestoneFactory.create(name="test milestone timeline")
    user_watcher= factories.UserFactory()
    milestone.add_watcher(user_watcher)
    history_services.take_snapshot(milestone, user=milestone.owner, delete=True)
    project_timeline = service.get_project_timeline(milestone.project)
    assert project_timeline[0].event_type == "milestones.milestone.delete"
    assert project_timeline[0].data["milestone"]["name"] == "test milestone timeline"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "milestones.milestone.delete"
    assert user_watcher_timeline[0].data["milestone"]["name"] == "test milestone timeline"


def test_delete_user_story_timeline():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    user_watcher= factories.UserFactory()
    user_story.add_watcher(user_watcher)
    history_services.take_snapshot(user_story, user=user_story.owner, delete=True)
    project_timeline = service.get_project_timeline(user_story.project)
    assert project_timeline[0].event_type == "userstories.userstory.delete"
    assert project_timeline[0].data["userstory"]["subject"] == "test us timeline"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "userstories.userstory.delete"
    assert user_watcher_timeline[0].data["userstory"]["subject"] == "test us timeline"


def test_delete_issue_timeline():
    issue = factories.IssueFactory.create(subject="test issue timeline")
    user_watcher= factories.UserFactory()
    issue.add_watcher(user_watcher)
    history_services.take_snapshot(issue, user=issue.owner, delete=True)
    project_timeline = service.get_project_timeline(issue.project)
    assert project_timeline[0].event_type == "issues.issue.delete"
    assert project_timeline[0].data["issue"]["subject"] == "test issue timeline"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "issues.issue.delete"
    assert user_watcher_timeline[0].data["issue"]["subject"] == "test issue timeline"


def test_delete_task_timeline():
    task = factories.TaskFactory.create(subject="test task timeline")
    user_watcher= factories.UserFactory()
    task.add_watcher(user_watcher)
    history_services.take_snapshot(task, user=task.owner, delete=True)
    project_timeline = service.get_project_timeline(task.project)
    assert project_timeline[0].event_type == "tasks.task.delete"
    assert project_timeline[0].data["task"]["subject"] == "test task timeline"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "tasks.task.delete"
    assert user_watcher_timeline[0].data["task"]["subject"] == "test task timeline"


def test_delete_wiki_page_timeline():
    page = factories.WikiPageFactory.create(slug="test wiki page timeline")
    user_watcher= factories.UserFactory()
    page.add_watcher(user_watcher)
    history_services.take_snapshot(page, user=page.owner, delete=True)
    project_timeline = service.get_project_timeline(page.project)
    assert project_timeline[0].event_type == "wiki.wikipage.delete"
    assert project_timeline[0].data["wikipage"]["slug"] == "test wiki page timeline"
    user_watcher_timeline = service.get_profile_timeline(user_watcher)
    assert user_watcher_timeline[0].event_type == "wiki.wikipage.delete"
    assert user_watcher_timeline[0].data["wikipage"]["slug"] == "test wiki page timeline"


def test_delete_membership_timeline():
    membership = factories.MembershipFactory.create()
    membership.delete()
    project_timeline = service.get_project_timeline(membership.project)
    user_timeline = service.get_user_timeline(membership.user)
    assert project_timeline[0].event_type == "projects.membership.delete"
    assert project_timeline[0].data["project"]["id"] == membership.project.id
    assert project_timeline[0].data["user"]["id"] == membership.user.id
    assert user_timeline[0].event_type == "projects.membership.delete"
    assert user_timeline[0].data["project"]["id"] == membership.project.id
    assert user_timeline[0].data["user"]["id"] == membership.user.id


def test_comment_user_story_timeline():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    history_services.take_snapshot(user_story, user=user_story.owner,
                                   comment="testing comment")
    project_timeline = service.get_project_timeline(user_story.project)
    assert project_timeline[0].event_type == "userstories.userstory.change"
    assert project_timeline[0].data["userstory"]["subject"] \
        == "test us timeline"
    assert project_timeline[0].data["comment"] == "testing comment"


def test_owner_user_story_timeline():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_user_timeline(user_story.owner)
    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[0].data["userstory"]["subject"] == "test us timeline"


def test_assigned_to_user_story_timeline():
    membership = factories.MembershipFactory.create()
    user_story = factories.UserStoryFactory.create(subject="test us timeline",
                                                   assigned_to=membership.user,
                                                   project=membership.project)
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_profile_timeline(user_story.assigned_to)
    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[0].data["userstory"]["subject"] == "test us timeline"


def test_due_date_user_story_timeline():
    initial_due_date = timezone.now() + timedelta(days=1)
    membership = factories.MembershipFactory.create()
    user_story = factories.UserStoryFactory.create(subject="test us timeline",
                                                   due_date=initial_due_date,
                                                   project=membership.project)
    history_services.take_snapshot(user_story, user=user_story.owner)

    new_due_date = timezone.now() + timedelta(days=3)
    user_story.due_date = new_due_date
    user_story.save()

    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_profile_timeline(user_story.owner)

    assert user_timeline[0].event_type == "userstories.userstory.change"
    assert user_timeline[0].data["values_diff"]['due_date'] == [str(initial_due_date.date()),
                                                                str(new_due_date.date())]


def test_assigned_users_user_story_timeline():
    membership = factories.MembershipFactory.create()
    user_story = factories.UserStoryFactory.create(subject="test us timeline",
                                                   project=membership.project)
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_profile_timeline(user_story.owner)

    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[0].data["userstory"]["subject"] == "test us timeline"

    user_story.assigned_to = membership.user
    user_story.assigned_users.set([membership.user])
    user_story.save()

    history_services.take_snapshot(user_story, user=user_story.owner)

    user_timeline = service.get_profile_timeline(user_story.owner)

    assert user_timeline[0].event_type == "userstories.userstory.change"
    assert "assigned_to" not in user_timeline[0].data["values_diff"].keys()
    assert user_timeline[0].data["values_diff"]['assigned_users'] == \
        [None, membership.user.username]


def test_user_data_for_non_system_users():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    project_timeline = service.get_project_timeline(user_story.project)
    serialized_obj = TimelineSerializer(project_timeline[0])
    serialized_obj.data["data"]["user"]["is_profile_visible"] = True


def test_user_data_for_system_users():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    user_story.owner.is_system = True
    user_story.owner.save()
    history_services.take_snapshot(user_story, user=user_story.owner)
    project_timeline = service.get_project_timeline(user_story.project)
    serialized_obj = TimelineSerializer(project_timeline[0])
    serialized_obj.data["data"]["user"]["is_profile_visible"] = False


def test_user_data_for_unactived_users():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    user_story.owner.cancel()
    user_story.owner.save()
    history_services.take_snapshot(user_story, user=user_story.owner)
    project_timeline = service.get_project_timeline(user_story.project)
    serialized_obj = TimelineSerializer(project_timeline[0])
    serialized_obj.data["data"]["user"]["is_profile_visible"] = False
    serialized_obj.data["data"]["user"]["username"] = "deleted-user"


def test_timeline_error_use_member_ids_instead_of_memberships_ids():
    user_story = factories.UserStoryFactory.create(
        subject="test error use member ids instead of "
                "memberships ids")

    member_user = user_story.owner
    external_user = factories.UserFactory.create()

    membership = factories.MembershipFactory.create(project=user_story.project,
                                                    user=member_user,
                                                    id=external_user.id)

    history_services.take_snapshot(user_story, user=member_user)

    user_timeline = service.get_profile_timeline(member_user)

    assert len(user_timeline) == 3
    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[1].event_type == "projects.membership.create"
    assert user_timeline[2].event_type == "users.user.create"

    external_user_timeline = service.get_profile_timeline(external_user)
    assert len(external_user_timeline) == 1
    assert external_user_timeline[0].event_type == "users.user.create"


def test_epic_related_uss():
    Timeline.objects.all().delete()

    # Users
    public_project_owner = factories.UserFactory.create(username="Public project's owner")
    not_qualified_private_project_member = factories.UserFactory.create(username="Unprivileged private role member")
    private_project_owner = factories.UserFactory.create(username="Privileged private role member")

    # A public project, containing a public epic which contains a private us from a private project
    public_project = factories.ProjectFactory.create(is_private=False,
                                                     owner=public_project_owner,
                                                     anon_permissions=[],
                                                     public_permissions=["view_us"])
    factories.MembershipFactory.create(project=public_project, user=public_project.owner, is_admin=True)
    public_epic = factories.EpicFactory.create(project=public_project, owner=public_project_owner)
    public_us = factories.UserStoryFactory.create(project=public_project, owner=public_project_owner)
    related_public_us = factories.RelatedUserStory.create(epic=public_epic, user_story=public_us)

    # A private project, containing the private user story related to the public epic from the public project
    private_project = factories.ProjectFactory.create(is_private=True,
                                                      owner=private_project_owner,
                                                      anon_permissions=[],
                                                      public_permissions=[])
    not_qualified_role = factories.RoleFactory(project=private_project, permissions=[])
    qualified_role = factories.RoleFactory(project=private_project, permissions=["view_us"])
    factories.MembershipFactory.create(project=private_project,
                                       user=not_qualified_private_project_member,
                                       role=not_qualified_role)
    factories.MembershipFactory.create(project=private_project,
                                       user=private_project_owner,
                                       role=qualified_role)
    private_us = factories.UserStoryFactory.create(project=private_project, owner=private_project_owner)
    related_private_us = factories.RelatedUserStory.create(epic=public_epic, user_story=private_us)

    service.register_timeline_implementation("epics.relateduserstory", "test", lambda x, extra_data=None: id(x))
    project_namespace = build_project_namespace(public_project)
    # Timeline entries regarding the first epic-related public US, for both a user and a project namespace
    service._add_to_object_timeline(public_project, related_public_us, "create", timezone.now(), project_namespace)
    service._add_to_object_timeline(public_project_owner, related_public_us, "create", timezone.now(),
                                    build_user_namespace(public_project_owner))
    # Timeline entries regarding the first epic-related private US, for both a user and a project namespace
    service._add_to_object_timeline(public_project, related_private_us, "create", timezone.now(), project_namespace)
    service._add_to_object_timeline(private_project_owner, related_private_us, "create", timezone.now(),
                                    build_user_namespace(private_project_owner))

    """
    # A list of users for the test iterations
    #
    # [index0] An anonymous user, who doesn't even have rights to see neither public nor private related USs.
    # [index1] A public project's owner, who related a public US to an epic from her own public project. She just
    #   has privileges to see her public related USs, and is a simple registered user regarding the private project.
    # [index2] An unprivileged private member, whose role doesn't have access to the private project's USs,
    #   but is able to view the related-USs from the public project's.
    # [index3] A private project's owner, who linked her private US to an epic from the public project.
                She has privileges to see any related USs.
    """
    users = [AnonymousUser(),  # [index 0]
             public_project_owner,  # [index 1]
             not_qualified_private_project_member,  # [index 2]
             private_project_owner]  # [index 3]

    timeline_counters = _helper_get_timelines_for_accessing_users(public_project, users)
    assert timeline_counters['project_timelines'] == [0, 1, 1, 2]
    assert timeline_counters['user_timelines'] == {
        # An anonymous user verifies the number of 'epics.relateduserstory' entries in the other users timelines
        #  She can't any epic related US on neither of [index1], [index2], or [index3] timelines
        0: [0, 0, 0],
        # An [index1] user verifies the number of 'epics.relateduserstory' entries in the other users timelines
        #  She can just see the public epic related USs on her own [index1] timeline
        1: [1, 0, 0],
        # An [index2] user verifies the number of 'epics.relateduserstory' entries in the other users timelines
        #  She can just see the public epic related USs on her own [index1] timeline
        2: [1, 0, 0],
        # An [index3] user verifies the number of 'epics.relateduserstory' entries in the other users timelines
        #  She can see both the public epic related USs in [index1] timeline, and in her own [index3] timeline
        3: [1, 0, 1]
    }


def _helper_get_timelines_for_accessing_users(project, users):
    """
    Get the number of timeline entries (of 'epics.relateduserstory' type) that the accessing users are able to see,
    for both a given project's timeline and the user's timelines
    :param project: the project with the epic which contains the related user stories
    :param users: both the accessing users, and the users from which recover their (user) timelines
    :return: Dict with counters for 'epics.relateduserstory' entries for both the (project) and (users)
    timelines, according to the accessing users privileges
    """
    timeline_counts = {'project_timelines': [], 'user_timelines': {}}
    # An anonymous user doesn't have a timeline to be recovered
    timeline_users = list(filter(lambda au: au != AnonymousUser(), users))

    for accessing_user in users:
        project_timeline = service.get_project_timeline(project, accessing_user)
        project_timeline = project_timeline.exclude(event_type__in=["projects.membership.create"])

        timeline_counts['project_timelines'].append(project_timeline.count())
        timeline_counts['user_timelines'][users.index(accessing_user)] = []

        for user in timeline_users:
            user_timeline = service.get_user_timeline(user, accessing_user)
            user_timeline = user_timeline.exclude(event_type__in=["users.user.create", "projects.membership.create"])

            timeline_counts['user_timelines'][users.index(accessing_user)].append(user_timeline.count())

    return timeline_counts
