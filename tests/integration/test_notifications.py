# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
import time
import base64
import datetime
import hashlib
import binascii
import struct
import pytz
import smtplib

from unittest.mock import Mock, MagicMock, patch

from django.urls import reverse
from django.utils import timezone

from django.apps import apps
from .. import factories as f

from taiga.base.api.settings import api_settings
from taiga.base.utils import json
from taiga.projects.notifications import services
from taiga.projects.notifications import models
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.notifications.choices import WebNotificationType
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import take_snapshot
from taiga.permissions.choices import MEMBERS_PERMISSIONS
from taiga.users.gravatar import get_user_gravatar_id

pytestmark = pytest.mark.django_db


@pytest.fixture
def mail():
    from django.core import mail
    mail.outbox = []
    return mail


@pytest.mark.parametrize(
    "header, expected",
    [
        ("", ""),
        ("One line", "One line"),
        ("Two \nlines", "Two lines"),
        ("Mix \r\nCR and LF \rin the string", "Mix CR and LF in the string"),
    ]
)
def test_remove_lr_cr(header, expected):
    rv = services.remove_lr_cr(header)
    assert rv == expected


def test_create_retrieve_notify_policy():
    project = f.ProjectFactory.create()

    policy_model_cls = apps.get_model("notifications", "NotifyPolicy")
    current_number = policy_model_cls.objects.all().count()
    assert current_number == 0

    policy = project.cached_notify_policy_for_user(project.owner)

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
    project = f.ProjectFactory.create()

    f.MembershipFactory(user=user1, project=project)

    issue = f.IssueFactory(
        project=project,
        description="Foo @{0} @{1} ".format(user1.username, user2.username),
    )
    issue.add_watcher = MagicMock()

    history = MagicMock()
    history.comment = ""

    services.analize_object_for_watchers(issue, history.comment, history.owner)
    assert issue.add_watcher.call_count == 1


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

    del project.cached_notify_policies
    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers
    issue.add_watcher(member3.user)
    policy_member3.notify_level = NotifyLevel.all
    policy_member3.save()

    del project.cached_notify_policies
    users = services.get_users_to_notify(issue)
    assert len(users) == 3
    assert users == {member1.user, member3.user, issue.get_owner()}

    # Test with watchers with ignore policy
    policy_member3.notify_level = NotifyLevel.none
    policy_member3.save()

    issue.add_watcher(member3.user)
    del project.cached_notify_policies
    users = services.get_users_to_notify(issue)
    assert len(users) == 2
    assert users == {member1.user, issue.get_owner()}

    # Test with watchers without permissions
    issue.add_watcher(member5.user)
    del project.cached_notify_policies
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
    watching_user_policy = project.cached_notify_policy_for_user(watching_user)
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
        project=project,
        user={"pk": member1.user.id},
        comment="test:change",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        project=project,
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
        project=project,
        user={"pk": member1.user.id},
        comment="test:change",
        type=HistoryType.change,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        project=project,
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
        project=project,
        user={"pk": member1.user.id},
        comment="test:change",
        type=HistoryType.change,
        key="issues.issue:{}".format(issue.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="issues.issue:{}".format(issue.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        project=project,
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
        project=project,
        user={"pk": member1.user.id},
        comment="test:change",
        type=HistoryType.change,
        key="wiki.wikipage:{}".format(wiki.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="wiki.wikipage:{}".format(wiki.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        project=project,
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

        # hashes should match for identical ids and times
        # we check the actual method in test_ms_thread_id()
        msg_time = headers.get('Message-ID').split('/')[2].split('@')[0]
        msg_ts = datetime.datetime.fromtimestamp(int(msg_time))
        assert services.make_ms_thread_index(in_reply_to, msg_ts) == headers.get('Thread-Index')


def test_send_notifications_on_unassigned(client, mail):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['modify_issue', 'view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    issue = f.IssueFactory.create(project=project,
                                  owner=member1.user,
                                  milestone=None,
                                  status=project.default_issue_status,
                                  severity=project.default_severity,
                                  priority=project.default_priority,
                                  type=project.default_issue_type)

    take_snapshot(issue, user=issue.owner)

    client.login(member1.user)
    url = reverse("issues-detail", args=[issue.pk])
    data = {
        "assigned_to": member2.user.id,
        "version": issue.version
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [member2.user.email]

    mail.outbox = []

    data = {
        "assigned_to": None,
        "version": issue.version + 1
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [member2.user.email]


def test_send_notifications_on_unassigned_and_notifications_are_disabled(client, mail):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['modify_issue', 'view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    member2_notify_policy = member2.user.notify_policies.get(project=project)
    member2_notify_policy.notify_level = NotifyLevel.none
    member2_notify_policy.save()

    issue = f.IssueFactory.create(project=project,
                                  owner=member1.user,
                                  milestone=None,
                                  status=project.default_issue_status,
                                  severity=project.default_severity,
                                  priority=project.default_priority,
                                  type=project.default_issue_type)

    take_snapshot(issue, user=issue.owner)

    client.login(member1.user)
    url = reverse("issues-detail", args=[issue.pk])
    data = {
        "assigned_to": member2.user.id,
        "version": issue.version
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 0

    mail.outbox = []

    data = {
        "assigned_to": None,
        "version": issue.version + 1
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 0



def test_not_send_notifications_on_unassigned_if_executer_and_unassigned_match(client, mail):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['modify_issue', 'view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    issue = f.IssueFactory.create(project=project,
                                  owner=member1.user,
                                  milestone=None,
                                  status=project.default_issue_status,
                                  severity=project.default_severity,
                                  priority=project.default_priority,
                                  type=project.default_issue_type)

    take_snapshot(issue, user=issue.owner)

    client.login(member1.user)
    url = reverse("issues-detail", args=[issue.pk])
    data = {
        "assigned_to": member1.user.id,
        "version": issue.version
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 0

    mail.outbox = []

    data = {
        "assigned_to": None,
        "version": issue.version + 1
    }
    response = client.json.patch(url, json.dumps(data))
    assert len(mail.outbox) == 0


def test_resource_notification_test(client, settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)
    role = f.RoleFactory.create(project=project, permissions=["view_issues"])
    f.MembershipFactory.create(project=project, user=user1, role=role, is_admin=True)
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
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_admin=True)
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
    data = {}
    data["id"] = None
    data["version"] = None
    data["watchers"] = [user1.pk, user2.pk]

    url = reverse("issues-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    issue = f.create_issue(project=project1, owner=user1)
    data = {}
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
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_admin=True)
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
    data = {
        "id": None,
        "version": None,
        "watchers": [user1.pk, user2.pk]
    }

    url = reverse("tasks-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    task = f.create_task(project=project1, owner=user1, status__project=project1, milestone__project=project1)
    data = {
        "id": None,
        "watchers": [user1.pk, user2.pk],
        "project": None
    }

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
    f.MembershipFactory.create(project=project1, user=user1, role=role1, is_admin=True)
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
    data = {
        "id": None,
        "version": None,
        "watchers": [user1.pk, user2.pk]
    }

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400

    # Test the impossible case when project is not
    # exists in create request, and validator works as expected
    us = f.create_userstory(project=project1, owner=user1, status__project=project1)
    data = {
        "id": None,
        "watchers": [user1.pk, user2.pk],
        "project": None
    }

    url = reverse("userstories-list")
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_retrieve_notify_policies_by_anonymous_user(client):
    project = f.ProjectFactory.create()

    policy = project.cached_notify_policy_for_user(project.owner)

    url = reverse("notifications-detail", args=[policy.pk])
    response = client.get(url, content_type="application/json")
    assert response.status_code == 404, response.status_code
    assert response.data["_error_message"] == "No NotifyPolicy matches the given query.", str(response.content)


def test_ms_thread_id():
    id = '<test/message@localhost>'
    now = timezone.now()

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
    ts = [datetime.datetime(1601, 1, 1, tzinfo=pytz.utc) + datetime.timedelta(microseconds=f//10)]

    # for the 5 byte appendixes that we won't use
    for n in range(22, len(s), 5):
        f = struct.unpack('>I', s[n:n+4])[0]
        ts.append(ts[-1] + datetime.timedelta(microseconds=(f << 18)//10))

    return guid, ts


def _notification_data(project, user, obj, content_type):
    return {
        "project": {
            "id": project.pk,
            "slug": project.slug,
            "name": project.name,
        },
        "obj": {
            "id": obj.pk,
            "ref": obj.ref,
            "subject": obj.subject,
            "content_type": content_type,
        },
        "user": {
            'big_photo': None,
            'date_joined': user.date_joined.strftime(
                api_settings.DATETIME_FORMAT),
            'gravatar_id': get_user_gravatar_id(user),
            'id': user.pk,
            'is_profile_visible': True,
            'name': user.get_full_name(),
            'photo': None,
            'username': user.username
        },
    }


def test_issue_updated_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_issues', 'modify_issue']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    member3 = f.MembershipFactory.create(project=project, role=role)
    member4 = f.MembershipFactory.create(project=project, role=role)
    issue = f.IssueFactory.create(project=project, owner=member1.user)

    client.login(member1.user)
    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path):
       client.patch(
            reverse("issues-detail", args=[issue.pk]),
            json.dumps({
                "description": "Lorem ipsum @%s dolor sit amet" %
                               member4.user.username,
                "assigned_to": member2.user.pk,
                "watchers": [member3.user.pk],
                "version": issue.version
            }),
            content_type="application/json"
        )

    assert 3 == models.WebNotification.objects.count()

    notifications = models.WebNotification.objects.all()
    notification_data = _notification_data(project, member1.user, issue,
                                           'issue')
    # Notification assigned_to
    assert notifications[0].user == member2.user
    assert notifications[0].event_type == WebNotificationType.assigned.value
    assert notifications[0].read is None
    assert notifications[0].data == notification_data

    # Notification added_as_watcher
    assert notifications[1].user == member3.user
    assert notifications[1].event_type == WebNotificationType.added_as_watcher
    assert notifications[1].read is None
    assert notifications[1].data == notification_data

    # Notification mentioned
    assert notifications[2].user == member4.user
    assert notifications[2].event_type == WebNotificationType.mentioned
    assert notifications[2].read is None
    assert notifications[2].data == notification_data


def test_comment_on_issue_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_issues', 'modify_issue']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    issue = f.IssueFactory.create(project=project, owner=member1.user)
    issue.add_watcher(member2.user)

    client.login(member1.user)
    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("issues-detail", args=[issue.pk]),
            json.dumps({
                "version": issue.version,
                "comment": "Lorem ipsum dolor sit amet",
            }),
            content_type="application/json"
        )

    assert 1 == models.WebNotification.objects.count()

    notification = models.WebNotification.objects.first()
    notification_data = _notification_data(project, member1.user, issue,
                                           'issue')

    # Notification comment
    assert notification.user == member2.user
    assert notification.event_type == WebNotificationType.comment
    assert notification.read is None
    assert notification.data == notification_data


def test_task_updated_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_tasks', 'modify_task']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    member3 = f.MembershipFactory.create(project=project, role=role)
    member4 = f.MembershipFactory.create(project=project, role=role)
    task = f.TaskFactory.create(project=project, owner=member1.user)

    client.login(member1.user)
    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("tasks-detail", args=[task.pk]),
            json.dumps({
                "description": "Lorem ipsum @%s dolor sit amet" %
                               member4.user.username,
                "assigned_to": member2.user.pk,
                "watchers": [member3.user.pk],
                "version": task.version
            }),
            content_type="application/json"
        )

    assert 3 == models.WebNotification.objects.count()

    notifications = models.WebNotification.objects.all()
    notification_data = _notification_data(project, member1.user, task, 'task')

    # Notification assigned_to
    assert notifications[0].user == member2.user
    assert notifications[0].event_type == WebNotificationType.assigned.value
    assert notifications[0].read is None
    assert notifications[0].data == notification_data

    # Notification added_as_watcher
    assert notifications[1].user == member3.user
    assert notifications[1].event_type == WebNotificationType.added_as_watcher
    assert notifications[1].read is None
    assert notifications[1].data == notification_data

    # Notification mentioned
    assert notifications[2].user == member4.user
    assert notifications[2].event_type == WebNotificationType.mentioned
    assert notifications[2].read is None
    assert notifications[2].data == notification_data


def test_comment_on_task_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_tasks', 'modify_task']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    task = f.TaskFactory.create(project=project, owner=member1.user)
    task.add_watcher(member2.user)

    client.login(member1.user)
    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("tasks-detail", args=[task.pk]),
            json.dumps({
                "version": task.version,
                "comment": "Lorem ipsum dolor sit amet",
            }),
            content_type="application/json"
        )

    assert 1 == models.WebNotification.objects.count()

    notification = models.WebNotification.objects.first()
    notification_data = _notification_data(project, member1.user, task, 'task')

    # Notification comment
    assert notification.user == member2.user
    assert notification.event_type == WebNotificationType.comment
    assert notification.read is None
    assert notification.data == notification_data


def test_us_updated_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_us', 'modify_us']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)
    member3 = f.MembershipFactory.create(project=project, role=role)
    member4 = f.MembershipFactory.create(project=project, role=role)

    us = f.create_userstory(
        project=project,
        owner=member1.user,
        assigned_to=member2.user,
        assigned_users =[],
        milestone=None
    )

    client.login(member1.user)
    mock_path = "taiga.projects.userstories.api.UserStoryViewSet." \
                "pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("userstories-detail", args=[us.pk]),
            json.dumps({
                "description": "Lorem ipsum @%s dolor sit amet" %
                               member4.user.username,
                "watchers": [member3.user.pk],
                "version": us.version
            }),
            content_type="application/json"
        )

    assert 2 == models.WebNotification.objects.count()

    notifications = models.WebNotification.objects.all()
    notification_data = _notification_data(project, member1.user, us,
                                           'userstory')

    # Notification added_as_watcher
    assert notifications[0].user == member3.user
    assert notifications[0].event_type == WebNotificationType.added_as_watcher
    assert notifications[0].read is None
    assert notifications[0].data == notification_data

    # Notification mentioned
    assert notifications[1].user == member4.user
    assert notifications[1].event_type == WebNotificationType.mentioned
    assert notifications[1].read is None
    assert notifications[1].data == notification_data


def test_us_updated_generates_web_notifications_asigned_users(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_us', 'modify_us']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    us = f.create_userstory(project=project, owner=member1.user, milestone=None)

    client.login(member1.user)
    mock_path = "taiga.projects.userstories.api.UserStoryViewSet." \
                "pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("userstories-detail", args=[us.pk]),
            json.dumps({
                "assigned_users": [member2.user.pk],
                "version": us.version
            }),
            content_type="application/json"
        )

    assert 1 == models.WebNotification.objects.count()

    notifications = models.WebNotification.objects.all()
    notification_data = _notification_data(project, member1.user, us, 'userstory')

    assert notifications[0].user == member2.user
    assert notifications[0].event_type == WebNotificationType.assigned.value
    assert notifications[0].read is None
    assert notifications[0].data == notification_data

def test_comment_on_us_generates_web_notifications(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(
        project=project,
        permissions=['view_us', 'modify_us']
    )
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    us = f.create_userstory(project=project, owner=member1.user, milestone=None)
    us.add_watcher(member2.user)

    client.login(member1.user)
    mock_path = "taiga.projects.userstories.api.UserStoryViewSet." \
                "pre_conditions_on_save"
    with patch(mock_path):
        client.patch(
            reverse("userstories-detail", args=[us.pk]),
            json.dumps({
                "version": us.version,
                "comment": "Lorem ipsum dolor sit amet",
            }),
            content_type="application/json"
        )

    assert 1 == models.WebNotification.objects.count()

    notification = models.WebNotification.objects.first()
    notification_data = _notification_data(project, member1.user, us,
                                           'userstory')

    # Notification comment
    assert notification.user == member2.user
    assert notification.event_type == WebNotificationType.comment
    assert notification.read is None
    assert notification.data == notification_data


def test_new_member_generates_web_notifications(client):
    project = f.ProjectFactory()
    john = f.UserFactory.create()
    joseph = f.UserFactory.create()
    other = f.UserFactory.create()
    tester = f.RoleFactory(project=project, name="Tester",
                           permissions=["view_project"])
    gamer = f.RoleFactory(project=project, name="Gamer",
                          permissions=["view_project"])
    f.MembershipFactory(project=project, user=john, role=tester, is_admin=True)

    # John and Other are members from another project
    project2 = f.ProjectFactory()
    f.MembershipFactory(project=project2, user=john, role=gamer, is_admin=True)
    f.MembershipFactory(project=project2, user=other, role=gamer)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": gamer.pk, "username": joseph.email},
            {"role_id": gamer.pk, "username": other.username},
        ]
    }
    client.login(john)
    client.json.post(url, json.dumps(data))

    assert models.WebNotification.objects.count() == 2

    notifications = models.WebNotification.objects.all()

    # Notification added_as_member
    assert notifications[0].user == joseph
    assert notifications[0].event_type == WebNotificationType.added_as_member
    assert notifications[0].read is None

    # Notification added_as_member
    assert notifications[1].user == other
    assert notifications[1].event_type == WebNotificationType.added_as_member
    assert notifications[1].read is None


def test_smtp_error_sending_notifications(settings, mail):
    settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL = 1

    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_issues', 'view_us', 'view_tasks', 'view_wiki_pages'])
    member1 = f.MembershipFactory.create(project=project, role=role)
    member2 = f.MembershipFactory.create(project=project, role=role)

    task = f.TaskFactory.create(project=project, owner=member2.user)
    history_change = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="test:change",
        type=HistoryType.change,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_create = f.HistoryEntryFactory.create(
        project=project,
        user={"pk": member1.user.id},
        comment="",
        type=HistoryType.create,
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    history_delete = f.HistoryEntryFactory.create(
        project=project,
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


    with patch("taiga.projects.notifications.services._make_template_mail") as make_template_email_mock, \
         patch("taiga.projects.notifications.services.logger") as logger_mock:
        email_mock = Mock()
        email_mock.send.side_effect = smtplib.SMTPDataError(msg="error smtp", code=123)
        make_template_email_mock.return_value = email_mock

        assert models.HistoryChangeNotification.objects.count() == 3
        assert len(mail.outbox) == 0
        time.sleep(1)
        services.process_sync_notifications()
        assert len(mail.outbox) == 0

        assert logger_mock.exception.call_count == 3
