# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from unittest import mock

from django.urls import reverse
from django.core import mail

from taiga.base.utils import json
from taiga.hooks.gogs import event_hooks
from taiga.hooks.gogs.api import GogsViewSet
from taiga.hooks.exceptions import ActionSyntaxException
from taiga.projects import choices as project_choices
from taiga.projects.epics.models import Epic
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.models import Membership
from taiga.projects.history.services import get_history_queryset_by_model_instance, take_snapshot
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.notifications.models import NotifyPolicy
from taiga.projects import services
from .. import factories as f

pytestmark = pytest.mark.django_db


def test_bad_signature(client):
    project = f.ProjectFactory()
    url = reverse("gogs-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = {
        "secret": "badbadbad"
    }
    response = client.post(url, json.dumps(data),
                           content_type="application/json")
    response_content = response.data
    assert response.status_code == 400
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gogs": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("gogs-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = {"test:": "data", "secret": "tpnIwJDz4e"}
    response = client.post(url, json.dumps(data),
                           content_type="application/json")

    assert response.status_code == 204


def test_blocked_project(client):
    project = f.ProjectFactory(blocked_code=project_choices.BLOCKED_BY_STAFF)
    f.ProjectModulesConfigFactory(project=project, config={
        "gogs": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("gogs-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = {"test:": "data", "secret": "tpnIwJDz4e"}
    response = client.post(url, json.dumps(data),
                           content_type="application/json")

    assert response.status_code == 451


def test_push_event_detected(client):
    project = f.ProjectFactory()
    url = reverse("gogs-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = {
        "commits": [
            {
                "message": "test message",
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }

    GogsViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(event_hooks.PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, json.dumps(data),
                               HTTP_X_GITHUB_EVENT="push",
                               content_type="application/json")

        assert process_event_mock.call_count == 1

    assert response.status_code == 204


def test_push_event_epic_processing(client):
    creation_status = f.EpicStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_epics"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.EpicStatusFactory(project=creation_status.project)
    epic = f.EpicFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #%s   ok
                    bye!
                """ % (epic.ref, new_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(epic.project, payload)
    ev_hook.process_event()
    epic = Epic.objects.get(id=epic.id)
    assert epic.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_issue_processing(client):
    creation_status = f.IssueStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_issues"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #%s   ok
                    bye!
                """ % (issue.ref, new_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    ev_hook.process_event()
    issue = Issue.objects.get(id=issue.id)
    assert issue.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_processing(client):
    creation_status = f.TaskStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_tasks"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.TaskStatusFactory(project=creation_status.project)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #%s   ok
                    bye!
                """ % (task.ref, new_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_user_story_processing(client):
    creation_status = f.UserStoryStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_us"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.UserStoryStatusFactory(project=creation_status.project)
    user_story = f.UserStoryFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #%s   ok
                    bye!
                """ % (user_story.ref, new_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }

    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    ev_hook.process_event()
    user_story = UserStory.objects.get(id=user_story.id)
    assert user_story.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_issue_mention(client):
    creation_status = f.IssueStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_issues"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    issue = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    take_snapshot(issue, user=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s   ok
                    bye!
                """ % (issue.ref),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    ev_hook.process_event()
    issue_history = get_history_queryset_by_model_instance(issue)
    assert issue_history.count() == 1
    assert issue_history[0].comment.startswith("This issue has been mentioned by")
    assert len(mail.outbox) == 1


def test_push_event_task_mention(client):
    creation_status = f.TaskStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_tasks"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    take_snapshot(task, user=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s   ok
                    bye!
                """ % (task.ref),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task_history = get_history_queryset_by_model_instance(task)
    assert task_history.count() == 1
    assert task_history[0].comment.startswith("This task has been mentioned by")
    assert len(mail.outbox) == 1


def test_push_event_user_story_mention(client):
    creation_status = f.UserStoryStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_us"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    user_story = f.UserStoryFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    take_snapshot(user_story, user=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s   ok
                    bye!
                """ % (user_story.ref),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }

    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    ev_hook.process_event()
    us_history = get_history_queryset_by_model_instance(user_story)
    assert us_history.count() == 1
    assert us_history[0].comment.startswith("This user story has been mentioned by")
    assert len(mail.outbox) == 1


def test_push_event_multiple_actions(client):
    creation_status = f.IssueStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_issues"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue1 = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    issue2 = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #%s   ok
                    test   TG-%s    #%s   ok
                    bye!
                """ % (issue1.ref, new_status.slug, issue2.ref, new_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook1 = event_hooks.PushEventHook(issue1.project, payload)
    ev_hook1.process_event()
    issue1 = Issue.objects.get(id=issue1.id)
    issue2 = Issue.objects.get(id=issue2.id)
    assert issue1.status.id == new_status.id
    assert issue2.status.id == new_status.id
    assert len(mail.outbox) == 2


def test_push_event_processing_case_insensitive(client):
    creation_status = f.TaskStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_tasks"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.TaskStatusFactory(project=creation_status.project)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = {
        "commits": [
            {
                "message": """test message
                    test   tg-%s    #%s   ok
                    bye!
                """ % (task.ref, new_status.slug.upper()),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_bad_processing_non_existing_ref(client):
    issue_status = f.IssueStatusFactory()
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-6666666    #%s   ok
                    bye!
                """ % (issue_status.slug),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }
    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue_status.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The referenced element doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_us_bad_processing_non_existing_status(client):
    user_story = f.UserStoryFactory.create()
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #non-existing-slug   ok
                    bye!
                """ % (user_story.ref),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_bad_processing_non_existing_status(client):
    issue = f.IssueFactory.create()
    payload = {
        "commits": [
            {
                "message": """test message
                    test   TG-%s    #non-existing-slug   ok
                    bye!
                """ % (issue.ref),
                "author": {
                    "username": "test",
                },
            }
        ],
        "repository": {
            "html_url": "http://test-url/test/project"
        }
    }

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_api_get_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 200
    content = response.data
    assert "gogs" in content
    assert content["gogs"]["secret"] != ""
    assert content["gogs"]["webhooks_url"] != ""


def test_api_patch_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    data = {
        "gogs": {
            "secret": "test_secret",
            "html_url": "test_url",
        }
    }
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 204

    config = services.get_modules_config(project).config
    assert "gogs" in config
    assert config["gogs"]["secret"] == "test_secret"
    assert config["gogs"]["webhooks_url"] != "test_url"


def test_replace_gogs_references():
    ev_hook = event_hooks.BaseGogsEventHook
    assert ev_hook.replace_gogs_references(None, "project-url", "#2") == "[Gogs#2](project-url/issues/2)"
    assert ev_hook.replace_gogs_references(None, "project-url", "#2 ") == "[Gogs#2](project-url/issues/2) "
    assert ev_hook.replace_gogs_references(None, "project-url", " #2 ") == " [Gogs#2](project-url/issues/2) "
    assert ev_hook.replace_gogs_references(None, "project-url", " #2") == " [Gogs#2](project-url/issues/2)"
    assert ev_hook.replace_gogs_references(None, "project-url", "#test") == "#test"
    assert ev_hook.replace_gogs_references(None, "project-url", None) == ""
