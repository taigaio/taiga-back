import pytest
import urllib

from unittest import mock

from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings

from taiga.base.utils import json
from taiga.hooks.bitbucket import event_hooks
from taiga.hooks.bitbucket.api import BitBucketViewSet
from taiga.hooks.exceptions import ActionSyntaxException
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects import services
from .. import factories as f

pytestmark = pytest.mark.django_db


def test_bad_signature(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "bitbucket": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("bitbucket-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "badbadbad")
    data = {}
    response = client.post(url, urllib.parse.urlencode(data, True), content_type="application/x-www-form-urlencoded")
    response_content = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 400
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "bitbucket": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("bitbucket-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {'payload': ['{"commits": []}']}
    response = client.post(url,
                           urllib.parse.urlencode(data, True),
                           content_type="application/x-www-form-urlencoded",
                           REMOTE_ADDR=settings.BITBUCKET_VALID_ORIGIN_IPS[0])
    assert response.status_code == 204


def test_invalid_ip(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "bitbucket": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("bitbucket-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {'payload': ['{"commits": []}']}
    response = client.post(url,
                           urllib.parse.urlencode(data, True),
                           content_type="application/x-www-form-urlencoded",
                           REMOTE_ADDR="111.111.111.112")
    assert response.status_code == 400


def test_not_ip_filter(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "bitbucket": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": []
        }
    })

    url = reverse("bitbucket-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {'payload': ['{"commits": []}']}
    response = client.post(url,
                           urllib.parse.urlencode(data, True),
                           content_type="application/x-www-form-urlencoded",
                           REMOTE_ADDR="111.111.111.112")
    assert response.status_code == 204


def test_push_event_detected(client):
    project = f.ProjectFactory()
    url = reverse("bitbucket-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = {'payload': ['{"commits": [{"message": "test message"}]}']}

    BitBucketViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(event_hooks.PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, urllib.parse.urlencode(data, True),
                               content_type="application/x-www-form-urlencoded")

        assert process_event_mock.call_count == 1

    assert response.status_code == 204


def test_push_event_issue_processing(client):
    creation_status = f.IssueStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_issues"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #%s   ok   bye!"}]}' % (issue.ref, new_status.slug)
    ]
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
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #%s   ok   bye!"}]}' % (task.ref, new_status.slug)
    ]
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
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #%s   ok   bye!"}]}' % (user_story.ref, new_status.slug)
    ]
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    ev_hook.process_event()
    user_story = UserStory.objects.get(id=user_story.id)
    assert user_story.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_multiple_actions(client):
    creation_status = f.IssueStatusFactory()
    role = f.RoleFactory(project=creation_status.project, permissions=["view_issues"])
    f.MembershipFactory(project=creation_status.project, role=role, user=creation_status.project.owner)
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue1 = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    issue2 = f.IssueFactory.create(status=creation_status, project=creation_status.project, owner=creation_status.project.owner)
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #%s   ok  test   TG-%s    #%s   ok  bye!"}]}' % (issue1.ref, new_status.slug, issue2.ref, new_status.slug)
    ]
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
    payload = [
        '{"commits": [{"message": "test message   test   tg-%s    #%s   ok   bye!"}]}' % (task.ref, new_status.slug.upper())
    ]
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_bad_processing_non_existing_ref(client):
    issue_status = f.IssueStatusFactory()
    payload = [
        '{"commits": [{"message": "test message   test   TG-6666666    #%s   ok   bye!"}]}' % (issue_status.slug)
    ]
    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue_status.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The referenced element doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_us_bad_processing_non_existing_status(client):
    user_story = f.UserStoryFactory.create()
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #non-existing-slug   ok   bye!"}]}' % (user_story.ref)
    ]

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_bad_processing_non_existing_status(client):
    issue = f.IssueFactory.create()
    payload = [
        '{"commits": [{"message": "test message   test   TG-%s    #non-existing-slug   ok   bye!"}]}' % (issue.ref)
    ]
    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_api_get_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_owner=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 200
    content = json.loads(response.content.decode("utf-8"))
    assert "bitbucket" in content
    assert content["bitbucket"]["secret"] != ""
    assert content["bitbucket"]["webhooks_url"] != ""


def test_api_patch_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_owner=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    data = {
        "bitbucket": {
            "secret": "test_secret",
            "url": "test_url",
        }
    }
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 204

    config = services.get_modules_config(project).config
    assert "bitbucket" in config
    assert config["bitbucket"]["secret"] == "test_secret"
    assert config["bitbucket"]["webhooks_url"] != "test_url"


def test_replace_bitbucket_references():
    assert event_hooks.replace_bitbucket_references("project-url", "#2") == "[BitBucket#2](project-url/issues/2)"
    assert event_hooks.replace_bitbucket_references("project-url", "#2 ") == "[BitBucket#2](project-url/issues/2) "
    assert event_hooks.replace_bitbucket_references("project-url", " #2 ") == " [BitBucket#2](project-url/issues/2) "
    assert event_hooks.replace_bitbucket_references("project-url", " #2") == " [BitBucket#2](project-url/issues/2)"
    assert event_hooks.replace_bitbucket_references("project-url", "#test") == "#test"
