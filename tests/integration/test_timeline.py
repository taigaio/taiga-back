# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

import pytest

from .. import factories

from taiga.projects.history import services as history_services
from taiga.timeline import service
from taiga.timeline.models import Timeline
from taiga.timeline.serializers import TimelineSerializer


pytestmark = pytest.mark.django_db


def test_add_to_object_timeline():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    task = factories.TaskFactory()

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))

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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))

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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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

    service.register_timeline_implementation("tasks.task", "test", lambda x, extra_data=None: str(id(x)))
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
    history_services.take_snapshot(user_story, user=user_story.owner, comment="testing comment")
    project_timeline = service.get_project_timeline(user_story.project)
    assert project_timeline[0].event_type == "userstories.userstory.change"
    assert project_timeline[0].data["userstory"]["subject"] == "test us timeline"
    assert project_timeline[0].data["comment"] == "testing comment"


def test_owner_user_story_timeline():
    user_story = factories.UserStoryFactory.create(subject="test us timeline")
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_user_timeline(user_story.owner)
    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[0].data["userstory"]["subject"] == "test us timeline"


def test_assigned_to_user_story_timeline():
    membership = factories.MembershipFactory.create()
    user_story = factories.UserStoryFactory.create(subject="test us timeline", assigned_to=membership.user, project=membership.project)
    history_services.take_snapshot(user_story, user=user_story.owner)
    user_timeline = service.get_profile_timeline(user_story.assigned_to)
    assert user_timeline[0].event_type == "userstories.userstory.create"
    assert user_timeline[0].data["userstory"]["subject"] == "test us timeline"


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
    user_story = factories.UserStoryFactory.create(subject="test error use member ids instead of "
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
