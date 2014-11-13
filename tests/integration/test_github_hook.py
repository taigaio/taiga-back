import pytest
import json

from unittest import mock

from django.core.urlresolvers import reverse
from django.core import mail

from taiga.github_hook.api import GitHubViewSet
from taiga.github_hook import event_hooks
from taiga.github_hook.exceptions import ActionSyntaxException
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
    project=f.ProjectFactory()
    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {}
    response = client.post(url, json.dumps(data),
        HTTP_X_HUB_SIGNATURE="sha1=badbadbad",
        content_type="application/json")
    response_content = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 400
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    project=f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "github": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {"test:": "data"}
    response = client.post(url, json.dumps(data),
        HTTP_X_HUB_SIGNATURE="sha1=3c8e83fdaa266f81c036ea0b71e98eb5e054581a",
        content_type="application/json")

    assert response.status_code == 200


def test_push_event_detected(client):
    project=f.ProjectFactory()
    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {"commits": [
      {"message": "test message"},
    ]}

    GitHubViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(event_hooks.PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, json.dumps(data),
            HTTP_X_GITHUB_EVENT="push",
            content_type="application/json")

        assert process_event_mock.call_count == 1

    assert response.status_code == 200


def test_push_event_issue_processing(client):
    creation_status = f.IssueStatusFactory()
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue = f.IssueFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(issue.ref, new_status.slug)},
    ]}
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    ev_hook.process_event()
    issue = Issue.objects.get(id=issue.id)
    assert issue.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_processing(client):
    creation_status = f.TaskStatusFactory()
    new_status = f.TaskStatusFactory(project=creation_status.project)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(task.ref, new_status.slug)},
    ]}
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_user_story_processing(client):
    creation_status = f.UserStoryStatusFactory()
    new_status = f.UserStoryStatusFactory(project=creation_status.project)
    user_story = f.UserStoryFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(user_story.ref, new_status.slug)},
    ]}

    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    ev_hook.process_event()
    user_story = UserStory.objects.get(id=user_story.id)
    assert user_story.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_processing_case_insensitive(client):
    creation_status = f.TaskStatusFactory()
    new_status = f.TaskStatusFactory(project=creation_status.project)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   tg-%s    #%s   ok
            bye!
        """%(task.ref, new_status.slug.upper())},
    ]}
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_bad_processing_non_existing_ref(client):
    issue_status = f.IssueStatusFactory()
    payload = {"commits": [
        {"message": """test message
            test   TG-6666666    #%s   ok
            bye!
        """%(issue_status.slug)},
    ]}
    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue_status.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The referenced element doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_us_bad_processing_non_existing_status(client):
    user_story = f.UserStoryFactory.create()
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #non-existing-slug   ok
            bye!
        """%(user_story.ref)},
    ]}

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_bad_processing_non_existing_status(client):
    issue = f.IssueFactory.create()
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #non-existing-slug   ok
            bye!
        """%(issue.ref)},
    ]}

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_issues_event_opened_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()
    Membership.objects.create(user=issue.owner, project=issue.project, role=f.RoleFactory.create(project=issue.project), is_owner=True)
    notify_policy = NotifyPolicy.objects.get(user=issue.owner, project=issue.project)
    notify_policy.notify_level = NotifyLevel.watch
    notify_policy.save()

    payload = {
        "action": "opened",
        "issue": {
            "title": "test-title",
            "body": "test-body",
            "number": 10,
        },
        "assignee": {},
        "label": {},
        "repository": {
            "html_url": "test",
        },
    }

    mail.outbox = []

    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)
    ev_hook.process_event()

    assert Issue.objects.count() == 2
    assert len(mail.outbox) == 1

def test_issues_event_other_than_opened_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()

    payload = {
        "action": "closed",
        "issue": {
            "title": "test-title",
            "body": "test-body",
            "number": 10,
        },
        "assignee": {},
        "label": {},
    }

    mail.outbox = []

    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)
    ev_hook.process_event()

    assert Issue.objects.count() == 1
    assert len(mail.outbox) == 0

def test_issues_event_bad_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()

    payload = {
        "action": "opened",
        "issue": {},
        "assignee": {},
        "label": {},
    }
    mail.outbox = []

    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)

    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "Invalid issue information"

    assert Issue.objects.count() == 1
    assert len(mail.outbox) == 0


def test_issue_comment_event_on_existing_issue_task_and_us(client):
    issue = f.IssueFactory.create(external_reference=["github", "10"])
    take_snapshot(issue, user=issue.owner)
    task = f.TaskFactory.create(project=issue.project, external_reference=["github", "10"])
    take_snapshot(task, user=task.owner)
    us = f.UserStoryFactory.create(project=issue.project, external_reference=["github", "10"])
    take_snapshot(us, user=us.owner)

    payload = {
        "action": "created",
        "issue": {
            "number": 10,
        },
        "comment": {
            "body": "Test body",
        },
        "repository": {
            "html_url": "test",
        },
    }

    mail.outbox = []

    assert get_history_queryset_by_model_instance(issue).count() == 0
    assert get_history_queryset_by_model_instance(task).count() == 0
    assert get_history_queryset_by_model_instance(us).count() == 0

    ev_hook = event_hooks.IssueCommentEventHook(issue.project, payload)
    ev_hook.process_event()

    issue_history = get_history_queryset_by_model_instance(issue)
    assert issue_history.count() == 1
    assert issue_history[0].comment == "From GitHub:\n\nTest body"

    task_history = get_history_queryset_by_model_instance(task)
    assert task_history.count() == 1
    assert task_history[0].comment == "From GitHub:\n\nTest body"

    us_history = get_history_queryset_by_model_instance(us)
    assert us_history.count() == 1
    assert us_history[0].comment == "From GitHub:\n\nTest body"

    assert len(mail.outbox) == 3


def test_issue_comment_event_on_not_existing_issue_task_and_us(client):
    issue = f.IssueFactory.create(external_reference=["github", "10"])
    take_snapshot(issue, user=issue.owner)
    task = f.TaskFactory.create(project=issue.project, external_reference=["github", "10"])
    take_snapshot(task, user=task.owner)
    us = f.UserStoryFactory.create(project=issue.project, external_reference=["github", "10"])
    take_snapshot(us, user=us.owner)

    payload = {
        "action": "created",
        "issue": {
            "number": 11,
        },
        "comment": {
            "body": "Test body",
        },
        "repository": {
            "html_url": "test",
        },
    }

    mail.outbox = []

    assert get_history_queryset_by_model_instance(issue).count() == 0
    assert get_history_queryset_by_model_instance(task).count() == 0
    assert get_history_queryset_by_model_instance(us).count() == 0

    ev_hook = event_hooks.IssueCommentEventHook(issue.project, payload)
    ev_hook.process_event()

    assert get_history_queryset_by_model_instance(issue).count() == 0
    assert get_history_queryset_by_model_instance(task).count() == 0
    assert get_history_queryset_by_model_instance(us).count() == 0

    assert len(mail.outbox) == 0


def test_issues_event_bad_comment(client):
    issue = f.IssueFactory.create(external_reference=["github", "10"])
    take_snapshot(issue, user=issue.owner)

    payload = {
        "action": "other",
        "issue": {},
        "comment": {},
        "repository": {
            "html_url": "test",
        },
    }
    ev_hook = event_hooks.IssueCommentEventHook(issue.project, payload)

    mail.outbox = []

    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "Invalid issue comment information"

    assert Issue.objects.count() == 1
    assert len(mail.outbox) == 0


def test_api_get_project_modules(client):
    project = f.create_project()

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 200
    content = json.loads(response.content.decode("utf-8"))
    assert "github" in content
    assert content["github"]["secret"] != ""
    assert content["github"]["webhooks_url"] != ""


def test_api_patch_project_modules(client):
    project = f.create_project()

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    data = {
        "github": {
            "secret": "test_secret",
            "url": "test_url",
        }
    }
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 204

    config = services.get_modules_config(project).config
    assert "github" in config
    assert config["github"]["secret"] == "test_secret"
    assert config["github"]["webhooks_url"] != "test_url"

def test_replace_github_references():
    assert event_hooks.replace_github_references("project-url", "#2") == "[GitHub#2](project-url/issues/2)"
    assert event_hooks.replace_github_references("project-url", "#2 ") == "[GitHub#2](project-url/issues/2) "
    assert event_hooks.replace_github_references("project-url", " #2 ") == " [GitHub#2](project-url/issues/2) "
    assert event_hooks.replace_github_references("project-url", " #2") == " [GitHub#2](project-url/issues/2)"
    assert event_hooks.replace_github_references("project-url", "#test") == "#test"
