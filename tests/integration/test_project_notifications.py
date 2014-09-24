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
from unittest.mock import MagicMock, patch

from django.core.urlresolvers import reverse
from django.apps import apps
from .. import factories as f

from taiga.projects.notifications import services
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType


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
    users = services.get_users_to_notify(issue, history=history)
    assert len(users) == 1
    assert tuple(users)[0] == issue.get_owner()

    # Test watch notify level in one member
    policy1.notify_level = NotifyLevel.watch
    policy1.save()

    users = services.get_users_to_notify(issue, history=history)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers
    issue.watchers.add(member3.user)
    users = services.get_users_to_notify(issue, history=history)
    assert len(users) == 3
    assert users == {member1.user, member3.user, issue.get_owner()}

    # Test with watchers with ignore policy
    policy3.notify_level = NotifyLevel.ignore
    policy3.save()

    issue.watchers.add(member3.user)
    users = services.get_users_to_notify(issue, history=history)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}


def test_send_notifications_using_services_method(mail):
    project = f.ProjectFactory.create()
    member1 = f.MembershipFactory.create(project=project)
    member2 = f.MembershipFactory.create(project=project)

    history_change = MagicMock()
    history_change.owner = member1.user
    history_change.comment = ""
    history_change.type = HistoryType.change

    history_create = MagicMock()
    history_create.owner = member1.user
    history_create.comment = ""
    history_create.type = HistoryType.create

    history_delete = MagicMock()
    history_delete.owner = member1.user
    history_delete.comment = ""
    history_delete.type = HistoryType.delete

    # Issues
    issue = f.IssueFactory.create(project=project)
    services.send_notifications(issue,
                                history=history_create,
                                users={member1.user, member2.user})

    services.send_notifications(issue,
                                history=history_change,
                                users={member1.user, member2.user})

    services.send_notifications(issue,
                                history=history_delete,
                                users={member1.user, member2.user})

    # Userstories
    us = f.UserStoryFactory.create()
    services.send_notifications(us,
                                history=history_create,
                                users={member1.user, member2.user})

    services.send_notifications(us,
                                history=history_change,
                                users={member1.user, member2.user})

    services.send_notifications(us,
                                history=history_delete,
                                users={member1.user, member2.user})
    # Tasks
    task = f.TaskFactory.create()
    services.send_notifications(task,
                                history=history_create,
                                users={member1.user, member2.user})

    services.send_notifications(task,
                                history=history_change,
                                users={member1.user, member2.user})

    services.send_notifications(task,
                                history=history_delete,
                                users={member1.user, member2.user})

    # Wiki pages
    wiki = f.WikiPageFactory.create()
    services.send_notifications(wiki,
                                history=history_create,
                                users={member1.user, member2.user})

    services.send_notifications(wiki,
                                history=history_change,
                                users={member1.user, member2.user})

    services.send_notifications(wiki,
                                history=history_delete,
                                users={member1.user, member2.user})

    assert len(mail.outbox) == 24



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
        assert len(mail.outbox) == 1
        assert response.status_code == 200

    with patch(mock_path) as m:
        response = client.delete(url)
        assert response.status_code == 204
        assert len(mail.outbox) == 2
