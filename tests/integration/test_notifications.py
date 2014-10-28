# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

import json
import pytest
import time
from unittest.mock import MagicMock, patch

from django.core.urlresolvers import reverse
from django.apps import apps
from .. import factories as f
from .. utils import set_settings

from taiga.projects.notifications import services
from taiga.projects.notifications import models
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import take_snapshot
from taiga.projects.issues.serializers import IssueSerializer
from taiga.projects.userstories.serializers import UserStorySerializer
from taiga.projects.tasks.serializers import TaskSerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def mail():
    from django.core import mail
    mail.outbox = []
    return mail


def test_attach_notify_policy_to_project_queryset():
    project1 = f.ProjectFactory.create()
    project2 = f.ProjectFactory.create()

    qs = project1.__class__.objects.order_by("id")
    qs = services.attach_notify_policy_to_project_queryset(project1.owner, qs)

    assert len(qs) == 2
    assert qs[0].notify_level == NotifyLevel.notwatch
    assert qs[1].notify_level == NotifyLevel.notwatch

    services.create_notify_policy(project1, project1.owner, NotifyLevel.watch)
    qs = project1.__class__.objects.order_by("id")
    qs = services.attach_notify_policy_to_project_queryset(project1.owner, qs)
    assert qs[0].notify_level == NotifyLevel.watch
    assert qs[1].notify_level == NotifyLevel.notwatch


def test_create_retrieve_notify_policy():
    project = f.ProjectFactory.create()

    policy_model_cls = apps.get_model("notifications", "NotifyPolicy")
    current_number = policy_model_cls.objects.all().count()
    assert current_number == 0

    policy = services.get_notify_policy(project, project.owner)

    current_number = policy_model_cls.objects.all().count()
    assert current_number == 1
    assert policy.notify_level == NotifyLevel.notwatch


def test_notify_policy_existence():
    project = f.ProjectFactory.create()
    assert not services.notify_policy_exists(project, project.owner)

    services.create_notify_policy(project, project.owner, NotifyLevel.watch)
    assert services.notify_policy_exists(project, project.owner)


def test_analize_object_for_watchers():
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()

    issue = MagicMock()
    issue.description = "Foo @{0} @{1} ".format(user1.username,
                                                user2.username)
    issue.content = ""

    history = MagicMock()
    history.comment = ""

    services.analize_object_for_watchers(issue, history)
    assert issue.watchers.add.call_count == 2


def test_users_to_notify():
    project = f.ProjectFactory.create()
    issue = f.IssueFactory.create(project=project)

    member1 = f.MembershipFactory.create(project=project)
    member2 = f.MembershipFactory.create(project=project)
    member3 = f.MembershipFactory.create(project=project)

    policy_model_cls = apps.get_model("notifications", "NotifyPolicy")

    policy1 = policy_model_cls.objects.get(user=member1.user)
    policy2 = policy_model_cls.objects.get(user=member2.user)
    policy3 = policy_model_cls.objects.get(user=member3.user)

    history = MagicMock()
    history.owner = member2.user
    history.comment = ""

    # Test basic description modifications
    issue.description = "test1"
    issue.save()
    users = services.get_users_to_notify(issue)
    assert len(users) == 1
    assert tuple(users)[0] == issue.get_owner()

    # Test watch notify level in one member
    policy1.notify_level = NotifyLevel.watch
    policy1.save()

    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers
    issue.watchers.add(member3.user)
    users = services.get_users_to_notify(issue)
    assert len(users) == 3
    assert users == {member1.user, member3.user, issue.get_owner()}

    # Test with watchers with ignore policy
    policy3.notify_level = NotifyLevel.ignore
    policy3.save()

    issue.watchers.add(member3.user)
    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

@set_settings(CHANGE_NOTIFICATIONS_MIN_INTERVAL=1)
def test_send_notifications_using_services_method(mail):
    project = f.ProjectFactory.create()
    member1 = f.MembershipFactory.create(project=project)
    member2 = f.MembershipFactory.create(project=project)

    history_change = MagicMock()
    history_change.user = {"pk": member1.user.pk}
    history_change.comment = ""
    history_change.type = HistoryType.change

    history_create = MagicMock()
    history_create.user = {"pk": member1.user.pk}
    history_create.comment = ""
    history_create.type = HistoryType.create

    history_delete = MagicMock()
    history_delete.user = {"pk": member1.user.pk}
    history_delete.comment = ""
    history_delete.type = HistoryType.delete

    # Issues
    issue = f.IssueFactory.create(project=project)
    take_snapshot(issue)
    services.send_notifications(issue,
                                history=history_create)

    services.send_notifications(issue,
                                history=history_change)

    services.send_notifications(issue,
                                history=history_delete)


    # Userstories
    us = f.UserStoryFactory.create()
    take_snapshot(us)
    services.send_notifications(us,
                                history=history_create)

    services.send_notifications(us,
                                history=history_change)

    services.send_notifications(us,
                                history=history_delete)

    # Tasks
    task = f.TaskFactory.create()
    take_snapshot(task)
    services.send_notifications(task,
                                history=history_create)

    services.send_notifications(task,
                                history=history_change)

    services.send_notifications(task,
                                history=history_delete)

    # Wiki pages
    wiki = f.WikiPageFactory.create()
    take_snapshot(wiki)
    services.send_notifications(wiki,
                                history=history_create)

    services.send_notifications(wiki,
                                history=history_change)

    services.send_notifications(wiki,
                                history=history_delete)

    assert models.HistoryChangeNotification.objects.count() == 12
    assert len(mail.outbox) == 0
    time.sleep(1)
    services.process_sync_notifications()
    assert len(mail.outbox) == 12

@set_settings(CHANGE_NOTIFICATIONS_MIN_INTERVAL=1)
def test_resource_notification_test(client, mail):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)
    role = f.RoleFactory.create(project=project)
    member1 = f.MembershipFactory.create(project=project, user=user1, role=role)
    member2 = f.MembershipFactory.create(project=project, user=user2, role=role)
    issue = f.IssueFactory.create(owner=user2, project=project)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    url = reverse("issues-detail", args=[issue.pk])

    client.login(user1)

    with patch(mock_path) as m:
        data = {"subject": "Fooooo", "version": issue.version}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
        assert len(mail.outbox) == 0
        assert models.HistoryChangeNotification.objects.count() == 1
        time.sleep(1)
        services.process_sync_notifications()
        assert len(mail.outbox) == 1
        assert models.HistoryChangeNotification.objects.count() == 0

    with patch(mock_path) as m:
        response = client.delete(url)
        assert response.status_code == 204
        assert len(mail.outbox) == 1
        assert models.HistoryChangeNotification.objects.count() == 1
        time.sleep(1)
        services.process_sync_notifications()
        assert len(mail.outbox) == 2
        assert models.HistoryChangeNotification.objects.count() == 0


def test_watchers_assignation_for_issue(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project1 = f.ProjectFactory.create(owner=user1)
    project2 = f.ProjectFactory.create(owner=user2)
    role1 = f.RoleFactory.create(project=project1)
    role2 = f.RoleFactory.create(project=project2)
    member1 = f.MembershipFactory.create(project=project1, user=user1, role=role1)
    member2 = f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    issue = f.create_issue(project=project1, owner=user1)
    data = {"version": issue.version,
            "watchers": [user1.pk]}

    url = reverse("issues-detail", args=[issue.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.content


    issue = f.create_issue(project=project1, owner=user1)
    data = {"version": issue.version,
            "watchers": [user1.pk, user2.pk]}

    url = reverse("issues-detail", args=[issue.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    issue = f.create_issue(project=project1, owner=user1)
    data = dict(IssueSerializer(issue).data)
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("issues-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    issue = f.create_issue(project=project1, owner=user1)
    data = dict(IssueSerializer(issue).data)

    data["id"] = None
    data["watchers"] = [user1.pk, user2.pk]
    data["project"] = None

    url = reverse("issues-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_watchers_assignation_for_task(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project1 = f.ProjectFactory.create(owner=user1)
    project2 = f.ProjectFactory.create(owner=user2)
    role1 = f.RoleFactory.create(project=project1)
    role2 = f.RoleFactory.create(project=project2)
    member1 = f.MembershipFactory.create(project=project1, user=user1, role=role1)
    member2 = f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    task = f.create_task(project=project1, owner=user1)
    data = {"version": task.version,
            "watchers": [user1.pk]}

    url = reverse("tasks-detail", args=[task.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.content


    task = f.create_task(project=project1, owner=user1)
    data = {"version": task.version,
            "watchers": [user1.pk, user2.pk]}

    url = reverse("tasks-detail", args=[task.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    task = f.create_task(project=project1, owner=user1)
    data = dict(TaskSerializer(task).data)
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("tasks-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    task = f.create_task(project=project1, owner=user1)
    data = dict(TaskSerializer(task).data)

    data["id"] = None
    data["watchers"] = [user1.pk, user2.pk]
    data["project"] = None

    url = reverse("tasks-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_watchers_assignation_for_us(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project1 = f.ProjectFactory.create(owner=user1)
    project2 = f.ProjectFactory.create(owner=user2)
    role1 = f.RoleFactory.create(project=project1)
    role2 = f.RoleFactory.create(project=project2)
    member1 = f.MembershipFactory.create(project=project1, user=user1, role=role1)
    member2 = f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    us = f.create_userstory(project=project1, owner=user1)
    data = {"version": us.version,
            "watchers": [user1.pk]}

    url = reverse("userstories-detail", args=[us.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200


    us = f.create_userstory(project=project1, owner=user1)
    data = {"version": us.version,
            "watchers": [user1.pk, user2.pk]}

    url = reverse("userstories-detail", args=[us.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    us = f.create_userstory(project=project1, owner=user1)
    data = dict(UserStorySerializer(us).data)
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    us = f.create_userstory(project=project1, owner=user1)
    data = dict(UserStorySerializer(us).data)

    data["id"] = None
    data["watchers"] = [user1.pk, user2.pk]
    data["project"] = None

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
