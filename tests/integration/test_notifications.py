# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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
import time
import math
import base64
import datetime
import hashlib
import binascii
import struct

from unittest.mock import MagicMock, patch

from django.core.urlresolvers import reverse
from django.apps import apps
from .. import factories as f

from taiga.base.utils import json
from taiga.projects.notifications import services
from taiga.projects.notifications import utils
from taiga.projects.notifications import models
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import take_snapshot
from taiga.projects.issues.serializers import IssueSerializer
from taiga.projects.userstories.serializers import UserStorySerializer
from taiga.projects.tasks.serializers import TaskSerializer
from taiga.permissions.permissions import MEMBERS_PERMISSIONS

pytestmark = pytest.mark.django_db


@pytest.fixture
def mail():
    from django.core import mail
    mail.outbox = []
    return mail


def test_attach_notify_level_to_project_queryset():
    project1 = f.ProjectFactory.create()
    f.ProjectFactory.create()

    qs = project1.__class__.objects.order_by("id")
    qs = utils.attach_notify_level_to_project_queryset(qs, project1.owner)

    assert len(qs) == 2
    assert qs[0].notify_level == NotifyLevel.involved
    assert qs[1].notify_level == NotifyLevel.involved

    services.create_notify_policy(project1, project1.owner, NotifyLevel.all)
    qs = project1.__class__.objects.order_by("id")
    qs = utils.attach_notify_level_to_project_queryset(qs, project1.owner)
    assert qs[0].notify_level == NotifyLevel.all
    assert qs[1].notify_level == NotifyLevel.involved


def test_create_retrieve_notify_policy():
    project = f.ProjectFactory.create()

    policy_model_cls = apps.get_model("notifications", "NotifyPolicy")
    current_number = policy_model_cls.objects.all().count()
    assert current_number == 0

    policy = services.get_notify_policy(project, project.owner)

    current_number = policy_model_cls.objects.all().count()
    assert current_number == 1
    assert policy.notify_level == NotifyLevel.involved


def test_notify_policy_existence():
    project = f.ProjectFactory.create()
    assert not services.notify_policy_exists(project, project.owner)

    services.create_notify_policy(project, project.owner, NotifyLevel.all)
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

    services.analize_object_for_watchers(issue, history.comment, history.owner)
    assert issue.add_watcher.call_count == 2


def test_analize_object_for_watchers_adding_owner_non_empty_comment():
    user1 = f.UserFactory.create()

    issue = MagicMock()
    issue.description = "Foo"
    issue.content = ""

    history = MagicMock()
    history.comment = "Comment"
    history.owner = user1

    services.analize_object_for_watchers(issue, history.comment, history.owner)
    assert issue.add_watcher.call_count == 1


def test_analize_object_for_watchers_no_adding_owner_empty_comment():
    user1 = f.UserFactory.create()

    issue = MagicMock()
    issue.description = "Foo"
    issue.content = ""

    history = MagicMock()
    history.comment = ""
    history.owner = user1

    services.analize_object_for_watchers(issue, history.comment, history.owner)
    assert issue.add_watcher.call_count == 0


def test_users_to_notify():
    project = f.ProjectFactory.create()
    role1 = f.RoleFactory.create(project=project, permissions=['view_issues'])
    role2 = f.RoleFactory.create(project=project, permissions=[])

    member1 = f.MembershipFactory.create(project=project, role=role1)
    policy_member1 = member1.user.notify_policies.get(project=project)
    policy_member1.notify_level = NotifyLevel.none
    policy_member1.save()
    member2 = f.MembershipFactory.create(project=project, role=role1)
    policy_member2 = member2.user.notify_policies.get(project=project)
    policy_member2.notify_level = NotifyLevel.none
    policy_member2.save()
    member3 = f.MembershipFactory.create(project=project, role=role1)
    policy_member3 = member3.user.notify_policies.get(project=project)
    policy_member3.notify_level = NotifyLevel.none
    policy_member3.save()
    member4 = f.MembershipFactory.create(project=project, role=role1)
    policy_member4 = member4.user.notify_policies.get(project=project)
    policy_member4.notify_level = NotifyLevel.none
    policy_member4.save()
    member5 = f.MembershipFactory.create(project=project, role=role2)
    policy_member5 = member5.user.notify_policies.get(project=project)
    policy_member5.notify_level = NotifyLevel.none
    policy_member5.save()
    inactive_member1 = f.MembershipFactory.create(project=project, role=role1)
    inactive_member1.user.is_active =  False
    inactive_member1.user.save()
    system_member1 = f.MembershipFactory.create(project=project, role=role1)
    system_member1.user.is_system = True
    system_member1.user.save()

    issue = f.IssueFactory.create(project=project, owner=member4.user)

    policy_model_cls = apps.get_model("notifications", "NotifyPolicy")

    policy_inactive_member1 = policy_model_cls.objects.get(user=inactive_member1.user)
    policy_inactive_member1.notify_level = NotifyLevel.all
    policy_inactive_member1.save()

    policy_system_member1 = policy_model_cls.objects.get(user=system_member1.user)
    policy_system_member1.notify_level = NotifyLevel.all
    policy_system_member1.save()

    history = MagicMock()
    history.owner = member2.user
    history.comment = ""

    # Test basic description modifications
    issue.description = "test1"
    issue.save()
    policy_member4.notify_level = NotifyLevel.all
    policy_member4.save()
    users = services.get_users_to_notify(issue)
    assert len(users) == 1
    assert tuple(users)[0] == issue.get_owner()

    # Test watch notify level in one member
    policy_member1.notify_level = NotifyLevel.all
    policy_member1.save()

    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers
    issue.add_watcher(member3.user)
    policy_member3.notify_level = NotifyLevel.all
    policy_member3.save()
    users = services.get_users_to_notify(issue)
    assert len(users) == 3
    assert users == {member1.user, member3.user, issue.get_owner()}

    # Test with watchers with ignore policy
    policy_member3.notify_level = NotifyLevel.none
    policy_member3.save()

    issue.add_watcher(member3.user)
    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers without permissions
    issue.add_watcher(member5.user)
    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with inactive user
    issue.add_watcher(inactive_member1.user)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with system user
    issue.add_watcher(system_member1.user)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}


def test_watching_users_to_notify_on_issue_modification_1():
    # If:
    # - the user is watching the issue
    # - the user is not watching the project
    # - the notify policy is watch
    # Then:
    # - email is sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    issue.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.all
    users = services.get_users_to_notify(issue)
    assert users == {watching_user, issue.owner}


def test_watching_users_to_notify_on_issue_modification_2():
    # If:
    # - the user is watching the issue
    # - the user is not watching the project
    # - the notify policy is involved
    # Then:
    # - email is sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    issue.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.involved
    users = services.get_users_to_notify(issue)
    assert users == {watching_user, issue.owner}


def test_watching_users_to_notify_on_issue_modification_3():
    # If:
    # - the user is watching the issue
    # - the user is not watching the project
    # - the notify policy is ignore
    # Then:
    # - email is not sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    issue.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.none
    watching_user_policy.save()
    users = services.get_users_to_notify(issue)
    assert users == {issue.owner}


def test_watching_users_to_notify_on_issue_modification_4():
    # If:
    # - the user is not watching the issue
    # - the user is watching the project
    # - the notify policy is ignore
    # Then:
    # - email is not sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    project.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.none
    watching_user_policy.save()
    users = services.get_users_to_notify(issue)
    assert users == {issue.owner}


def test_watching_users_to_notify_on_issue_modification_5():
    # If:
    # - the user is not watching the issue
    # - the user is watching the project
    # - the notify policy is watch
    # Then:
    # - email is sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    project.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.all
    watching_user_policy.save()
    users = services.get_users_to_notify(issue)
    assert users == {watching_user, issue.owner}


def test_watching_users_to_notify_on_issue_modification_6():
    # If:
    # - the user is not watching the issue
    # - the user is watching the project
    # - the notify policy is involved
    # Then:
    # - email is sent
    project = f.ProjectFactory.create(anon_permissions= ["view_issues"])
    issue = f.IssueFactory.create(project=project)
    watching_user = f.UserFactory()
    project.add_watcher(watching_user)
    watching_user_policy = services.get_notify_policy(project, watching_user)
    issue.description = "test1"
    issue.save()
    watching_user_policy.notify_level = NotifyLevel.involved
    watching_user_policy.save()
    users = services.get_users_to_notify(issue)
    assert users == {issue.owner}


def test_send_notifications_using_services_method_for_user_stories(settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    us = f.UserStoryFactory.create(project=project, owner=member2.user)
    history_change = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="test:delete",
        type=HistoryType.delete,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[]
    )

    take_snapshot(us, user=us.owner)
    services.send_notifications(us,
                                history=history_create)

    services.send_notifications(us,
                                history=history_change)

    services.send_notifications(us,
                                history=history_delete)

    assert models.HistoryChangeNotification.objects.count() == 3
    assert len(mail.outbox) == 0
    time.sleep(1)
    services.process_sync_notifications()
    assert len(mail.outbox) == 3

    # test headers
    domain = settings.SITES["api"]["domain"].split(":")[0] or settings.SITES["api"]["domain"]
    for msg in mail.outbox:
        m_id = "{project_slug}/{msg_id}".format(
            project_slug=project.slug,
            msg_id=us.ref
        )

        message_id = "<{m_id}/".format(m_id=m_id)
        message_id_domain = "@{domain}>".format(domain=domain)
        in_reply_to = "<{m_id}@{domain}>".format(m_id=m_id, domain=domain)
        list_id = "Taiga/{p_name} <taiga.{p_slug}@{domain}>" \
            .format(p_name=project.name, p_slug=project.slug, domain=domain)

        assert msg.extra_headers
        headers = msg.extra_headers

        # can't test the time part because it's set when sending
        # check what we can
        assert 'Message-ID' in headers
        assert message_id in headers.get('Message-ID')
        assert message_id_domain in headers.get('Message-ID')

        assert 'In-Reply-To' in headers
        assert in_reply_to == headers.get('In-Reply-To')
        assert 'References' in headers
        assert in_reply_to == headers.get('References')

        assert 'List-ID' in headers
        assert list_id == headers.get('List-ID')

        assert 'Thread-Index' in headers
        # always is b64 encoded 22 bytes
        assert len(base64.b64decode(headers.get('Thread-Index'))) == 22

        # hashes should match for identical ids and times
        # we check the actual method in test_ms_thread_id()
        msg_time = headers.get('Message-ID').split('/')[2].split('@')[0]
        msg_ts = datetime.datetime.fromtimestamp(int(msg_time))
        assert services.make_ms_thread_index(in_reply_to, msg_ts) == headers.get('Thread-Index')


def test_send_notifications_using_services_method_for_tasks(settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    task = f.TaskFactory.create(project=project, owner=member2.user)
    history_change = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.change,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="test:delete",
        type=HistoryType.delete,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    take_snapshot(task, user=task.owner)
    services.send_notifications(task,
                                history=history_create)

    services.send_notifications(task,
                                history=history_change)

    services.send_notifications(task,
                                history=history_delete)

    assert models.HistoryChangeNotification.objects.count() == 3
    assert len(mail.outbox) == 0
    time.sleep(1)
    services.process_sync_notifications()
    assert len(mail.outbox) == 3

    # test headers
    domain = settings.SITES["api"]["domain"].split(":")[0] or settings.SITES["api"]["domain"]
    for msg in mail.outbox:
        m_id = "{project_slug}/{msg_id}".format(
            project_slug=project.slug,
            msg_id=task.ref
        )

        message_id = "<{m_id}/".format(m_id=m_id)
        message_id_domain = "@{domain}>".format(domain=domain)
        in_reply_to = "<{m_id}@{domain}>".format(m_id=m_id, domain=domain)
        list_id = "Taiga/{p_name} <taiga.{p_slug}@{domain}>" \
            .format(p_name=project.name, p_slug=project.slug, domain=domain)

        assert msg.extra_headers
        headers = msg.extra_headers

        # can't test the time part because it's set when sending
        # check what we can
        assert 'Message-ID' in headers
        assert message_id in headers.get('Message-ID')
        assert message_id_domain in headers.get('Message-ID')

        assert 'In-Reply-To' in headers
        assert in_reply_to == headers.get('In-Reply-To')
        assert 'References' in headers
        assert in_reply_to == headers.get('References')

        assert 'List-ID' in headers
        assert list_id == headers.get('List-ID')

        assert 'Thread-Index' in headers
        # always is b64 encoded 22 bytes
        assert len(base64.b64decode(headers.get('Thread-Index'))) == 22

        # hashes should match for identical ids and times
        # we check the actual method in test_ms_thread_id()
        msg_time = headers.get('Message-ID').split('/')[2].split('@')[0]
        msg_ts = datetime.datetime.fromtimestamp(int(msg_time))
        assert services.make_ms_thread_index(in_reply_to, msg_ts) == headers.get('Thread-Index')


def test_send_notifications_using_services_method_for_issues(settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    issue = f.IssueFactory.create(project=project, owner=member2.user)
    history_change = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.change,
        key="issues.issue:{}".format(issue.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="issues.issue:{}".format(issue.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="test:delete",
        type=HistoryType.delete,
        key="issues.issue:{}".format(issue.id),
        is_hidden=False,
        diff=[]
    )

    take_snapshot(issue, user=issue.owner)
    services.send_notifications(issue,
                                history=history_create)

    services.send_notifications(issue,
                                history=history_change)

    services.send_notifications(issue,
                                history=history_delete)

    assert models.HistoryChangeNotification.objects.count() == 3
    assert len(mail.outbox) == 0
    time.sleep(1)
    services.process_sync_notifications()
    assert len(mail.outbox) == 3

    # test headers
    domain = settings.SITES["api"]["domain"].split(":")[0] or settings.SITES["api"]["domain"]
    for msg in mail.outbox:
        m_id = "{project_slug}/{msg_id}".format(
            project_slug=project.slug,
            msg_id=issue.ref
        )

        message_id = "<{m_id}/".format(m_id=m_id)
        message_id_domain = "@{domain}>".format(domain=domain)
        in_reply_to = "<{m_id}@{domain}>".format(m_id=m_id, domain=domain)
        list_id = "Taiga/{p_name} <taiga.{p_slug}@{domain}>" \
            .format(p_name=project.name, p_slug=project.slug, domain=domain)

        assert msg.extra_headers
        headers = msg.extra_headers

        # can't test the time part because it's set when sending
        # check what we can
        assert 'Message-ID' in headers
        assert message_id in headers.get('Message-ID')
        assert message_id_domain in headers.get('Message-ID')

        assert 'In-Reply-To' in headers
        assert in_reply_to == headers.get('In-Reply-To')
        assert 'References' in headers
        assert in_reply_to == headers.get('References')

        assert 'List-ID' in headers
        assert list_id == headers.get('List-ID')

        assert 'Thread-Index' in headers
        # always is b64 encoded 22 bytes
        assert len(base64.b64decode(headers.get('Thread-Index'))) == 22

        # hashes should match for identical ids and times
        # we check the actual method in test_ms_thread_id()
        msg_time = headers.get('Message-ID').split('/')[2].split('@')[0]
        msg_ts = datetime.datetime.fromtimestamp(int(msg_time))
        assert services.make_ms_thread_index(in_reply_to, msg_ts) == headers.get('Thread-Index')


def test_send_notifications_using_services_method_for_wiki_pages(settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    wiki = f.WikiPageFactory.create(project=project, owner=member2.user)
    history_change = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.change,
        key="wiki.wikipage:{}".format(wiki.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="wiki.wikipage:{}".format(wiki.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        user={"pk": member1.user.id},
        comment="test:delete",
        type=HistoryType.delete,
        key="wiki.wikipage:{}".format(wiki.id),
        is_hidden=False,
        diff=[]
    )
    take_snapshot(wiki, user=wiki.owner)
    services.send_notifications(wiki,
                                history=history_create)

    services.send_notifications(wiki,
                                history=history_change)

    services.send_notifications(wiki,
                                history=history_delete)

    assert models.HistoryChangeNotification.objects.count() == 3
    assert len(mail.outbox) == 0
    time.sleep(1)
    services.process_sync_notifications()
    assert len(mail.outbox) == 3

    # test headers
    domain = settings.SITES["api"]["domain"].split(":")[0] or settings.SITES["api"]["domain"]
    for msg in mail.outbox:
        m_id = "{project_slug}/{msg_id}".format(
            project_slug=project.slug,
            msg_id=wiki.slug
        )

        message_id = "<{m_id}/".format(m_id=m_id)
        message_id_domain = "@{domain}>".format(domain=domain)
        in_reply_to = "<{m_id}@{domain}>".format(m_id=m_id, domain=domain)
        list_id = "Taiga/{p_name} <taiga.{p_slug}@{domain}>" \
            .format(p_name=project.name, p_slug=project.slug, domain=domain)

        assert msg.extra_headers
        headers = msg.extra_headers

        # can't test the time part because it's set when sending
        # check what we can
        assert 'Message-ID' in headers
        assert message_id in headers.get('Message-ID')
        assert message_id_domain in headers.get('Message-ID')

        assert 'In-Reply-To' in headers
        assert in_reply_to == headers.get('In-Reply-To')
        assert 'References' in headers
        assert in_reply_to == headers.get('References')

        assert 'List-ID' in headers
        assert list_id == headers.get('List-ID')

        assert 'Thread-Index' in headers
        # always is b64 encoded 22 bytes
        assert len(base64.b64decode(headers.get('Thread-Index'))) == 22

        # hashes should match for identical ids and times
        # we check the actual method in test_ms_thread_id()
        msg_time = headers.get('Message-ID').split('/')[2].split('@')[0]
        msg_ts = datetime.datetime.fromtimestamp(int(msg_time))
        assert services.make_ms_thread_index(in_reply_to, msg_ts) == headers.get('Thread-Index')


def test_resource_notification_test(client, settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)
    role = f.RoleFactory.create(project=project, permissions=["view_issues"])
    f.MembershipFactory.create(project=project, user=user1, role=role, is_owner=True)
    f.MembershipFactory.create(project=project, user=user2, role=role)
    issue = f.IssueFactory.create(owner=user2, project=project)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    url = reverse("issues-detail", args=[issue.pk])

    client.login(user1)

    with patch(mock_path):
        data = {"subject": "Fooooo", "version": issue.version}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
        assert len(mail.outbox) == 0
        assert models.HistoryChangeNotification.objects.count() == 1
        time.sleep(1)
        services.process_sync_notifications()
        assert len(mail.outbox) == 1
        assert models.HistoryChangeNotification.objects.count() == 0

    with patch(mock_path):
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
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_owner=True)
    f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    issue = f.create_issue(project=project1, owner=user1)
    data = {"version": issue.version,
            "watchersa": [user1.pk]}

    url = reverse("issues-detail", args=[issue.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, str(response.content)

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
    role1 = f.RoleFactory.create(project=project1, permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    role2 = f.RoleFactory.create(project=project2)
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_owner=True)
    f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    task = f.create_task(project=project1, owner=user1, status__project=project1, milestone__project=project1, user_story=None)
    data = {"version": task.version,
            "watchers": [user1.pk]}

    url = reverse("tasks-detail", args=[task.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, str(response.content)

    task = f.create_task(project=project1, owner=user1, status__project=project1, milestone__project=project1)
    data = {"version": task.version,
            "watchers": [user1.pk, user2.pk]}

    url = reverse("tasks-detail", args=[task.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    task = f.create_task(project=project1, owner=user1, status__project=project1, milestone__project=project1)
    data = dict(TaskSerializer(task).data)
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("tasks-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    task = f.create_task(project=project1, owner=user1, status__project=project1, milestone__project=project1)
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
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_owner=True)
    f.MembershipFactory.create(project=project2, user=user2, role=role2)

    client.login(user1)

    us = f.create_userstory(project=project1, owner=user1, status__project=project1)
    data = {"version": us.version,
            "watchers": [user1.pk]}

    url = reverse("userstories-detail", args=[us.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, str(response.content)

    us = f.create_userstory(project=project1, owner=user1, status__project=project1)
    data = {"version": us.version,
            "watchers": [user1.pk, user2.pk]}

    url = reverse("userstories-detail", args=[us.pk])
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    us = f.create_userstory(project=project1, owner=user1, status__project=project1)
    data = dict(UserStorySerializer(us).data)
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    us = f.create_userstory(project=project1, owner=user1, status__project=project1)
    data = dict(UserStorySerializer(us).data)

    data["id"] = None
    data["watchers"] = [user1.pk, user2.pk]
    data["project"] = None

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_retrieve_notify_policies_by_anonymous_user(client):
    project = f.ProjectFactory.create()

    policy = services.get_notify_policy(project, project.owner)

    url = reverse("notifications-detail", args=[policy.pk])
    response = client.get(url, content_type="application/json")
    assert response.status_code == 404, response.status_code
    assert response.data["_error_message"] == "No NotifyPolicy matches the given query.", str(response.content)


def test_ms_thread_id():
    id = '<test/message@localhost>'
    now = datetime.datetime.now()

    index = services.make_ms_thread_index(id, now)
    parsed = parse_ms_thread_index(index)

    assert parsed[0] == hashlib.md5(id.encode('utf-8')).hexdigest()
    # always only one time
    assert (now - parsed[1][0]).seconds <= 2


# see http://stackoverflow.com/questions/27374077/parsing-thread-index-mail-header-with-python
def parse_ms_thread_index(index):
    s = base64.b64decode(index)

    # ours are always md5 digests
    guid = binascii.hexlify(s[6:22]).decode('utf-8')

    # if we had real guids, we'd do something like
    # guid = struct.unpack('>IHHQ', s[6:22])
    # guid = '%08X-%04X-%04X-%04X-%12X' % (guid[0], guid[1], guid[2], (guid[3] >> 48) & 0xFFFF, guid[3] & 0xFFFFFFFFFFFF)

    f = struct.unpack('>Q', s[:6] + b'\0\0')[0]
    ts = [datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=f//10)]

    # for the 5 byte appendixes that we won't use
    for n in range(22, len(s), 5):
        f = struct.unpack('>I', s[n:n+4])[0]
        ts.append(ts[-1] + datetime.timedelta(microseconds=(f << 18)//10))

    return guid, ts
