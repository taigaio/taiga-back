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
from copy import deepcopy

from unittest import mock

from django.core.urlresolvers import reverse
from django.core import mail

from taiga.base.utils import json
from taiga.hooks.gitlab import event_hooks
from taiga.hooks.gitlab.api import GitLabViewSet
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

push_base_payload = {
  "object_kind": "push",
  "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
  "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
  "ref": "refs/heads/master",
  "checkout_sha": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
  "user_id": 4,
  "user_name": "John Smith",
  "user_email": "john@example.com",
  "user_avatar": "https://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=8://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=80",
  "project_id": 15,
  "project": {
    "name": "Diaspora",
    "description": "",
    "web_url": "http://example.com/mike/diaspora",
    "avatar_url": None,
    "git_ssh_url": "git@example.com:mike/diaspora.git",
    "git_http_url": "http://example.com/mike/diaspora.git",
    "namespace": "Mike",
    "visibility_level": 0,
    "path_with_namespace": "mike/diaspora",
    "default_branch": "master",
    "homepage": "http://example.com/mike/diaspora",
    "url": "git@example.com:mike/diaspora.git",
    "ssh_url": "git@example.com:mike/diaspora.git",
    "http_url": "http://example.com/mike/diaspora.git"
  },
  "repository": {
    "name": "Diaspora",
    "url": "git@example.com:mike/diaspora.git",
    "description": "",
    "homepage": "http://example.com/mike/diaspora",
    "git_http_url": "http://example.com/mike/diaspora.git",
    "git_ssh_url": "git@example.com:mike/diaspora.git",
    "visibility_level": 0
  },
  "commits": [
    {
      "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
      "message": "Update Catalan translation to e38cb41.",
      "timestamp": "2011-12-12T14:27:31+02:00",
      "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
      "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
      "author": {
        "name": "Jordi Mallach",
        "email": "jordi@softcatala.org"
      },
      "added": ["CHANGELOG"],
      "modified": ["app/controller/application.rb"],
      "removed": []
    },
    {
      "id": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
      "message": "fixed readme",
      "timestamp": "2012-01-03T23:36:29+02:00",
      "url": "http://example.com/mike/diaspora/commit/da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
      "author": {
        "name": "GitLab dev user",
        "email": "gitlabdev@dv6700.(none)"
      },
      "added": ["CHANGELOG"],
      "modified": ["app/controller/application.rb"],
      "removed": []
    }
  ],
  "total_commits_count": 4
}

new_issue_base_payload = {
  "object_kind": "issue",
  "user": {
    "name": "Administrator",
    "username": "root",
    "avatar_url": "http://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon"
  },
  "project": {
    "name": "Gitlab Test",
    "description": "Aut reprehenderit ut est.",
    "web_url": "http://example.com/gitlabhq/gitlab-test",
    "avatar_url": None,
    "git_ssh_url": "git@example.com:gitlabhq/gitlab-test.git",
    "git_http_url": "http://example.com/gitlabhq/gitlab-test.git",
    "namespace": "GitlabHQ",
    "visibility_level": 20,
    "path_with_namespace": "gitlabhq/gitlab-test",
    "default_branch": "master",
    "homepage": "http://example.com/gitlabhq/gitlab-test",
    "url": "http://example.com/gitlabhq/gitlab-test.git",
    "ssh_url": "git@example.com:gitlabhq/gitlab-test.git",
    "http_url": "http://example.com/gitlabhq/gitlab-test.git"
  },
  "repository": {
    "name": "Gitlab Test",
    "url": "http://example.com/gitlabhq/gitlab-test.git",
    "description": "Aut reprehenderit ut est.",
    "homepage": "http://example.com/gitlabhq/gitlab-test"
  },
  "object_attributes": {
    "id": 301,
    "title": "New API: create/update/delete file",
    "assignee_id": 51,
    "author_id": 51,
    "project_id": 14,
    "created_at": "2013-12-03T17:15:43Z",
    "updated_at": "2013-12-03T17:15:43Z",
    "position": 0,
    "branch_name": None,
    "description": "Create new API for manipulations with repository",
    "milestone_id": None,
    "state": "opened",
    "iid": 23,
    "url": "http://example.com/diaspora/issues/23",
    "action": "open"
  },
  "assignee": {
    "name": "User1",
    "username": "user1",
    "avatar_url": "http://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon"
  }
}

issue_comment_base_payload = {
  "object_kind": "note",
  "user": {
    "name": "Administrator",
    "username": "root",
    "avatar_url": "http://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon"
  },
  "project_id": 5,
  "project": {
    "name": "Gitlab Test",
    "description": "Aut reprehenderit ut est.",
    "web_url": "http://example.com/gitlab-org/gitlab-test",
    "avatar_url": None,
    "git_ssh_url": "git@example.com:gitlab-org/gitlab-test.git",
    "git_http_url": "http://example.com/gitlab-org/gitlab-test.git",
    "namespace": "Gitlab Org",
    "visibility_level": 10,
    "path_with_namespace": "gitlab-org/gitlab-test",
    "default_branch": "master",
    "homepage": "http://example.com/gitlab-org/gitlab-test",
    "url": "http://example.com/gitlab-org/gitlab-test.git",
    "ssh_url": "git@example.com:gitlab-org/gitlab-test.git",
    "http_url": "http://example.com/gitlab-org/gitlab-test.git"
  },
  "repository": {
    "name": "diaspora",
    "url": "git@example.com:mike/diaspora.git",
    "description": "",
    "homepage": "http://example.com/mike/diaspora"
  },
  "object_attributes": {
    "id": 1241,
    "note": "Hello world",
    "noteable_type": "Issue",
    "author_id": 1,
    "created_at": "2015-05-17 17:06:40 UTC",
    "updated_at": "2015-05-17 17:06:40 UTC",
    "project_id": 5,
    "attachment": None,
    "line_code": None,
    "commit_id": "",
    "noteable_id": 92,
    "system": False,
    "st_diff": None,
    "url": "http://example.com/gitlab-org/gitlab-test/issues/17#note_1241"
  },
  "issue": {
    "id": 92,
    "title": "test",
    "assignee_id": None,
    "author_id": 1,
    "project_id": 5,
    "created_at": "2015-04-12 14:53:17 UTC",
    "updated_at": "2015-04-26 08:28:42 UTC",
    "position": 0,
    "branch_name": None,
    "description": "test",
    "milestone_id": None,
    "state": "closed",
    "iid": 17
  }
}

def test_bad_signature(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e"
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "badbadbad")
    data = {}
    response = client.post(url, json.dumps(data), content_type="application/json")
    response_content = response.data
    assert response.status_code == 400
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["111.111.111.111"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.111")

    assert response.status_code == 204


def test_ok_empty_payload(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["111.111.111.111"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    response = client.post(url, "null", content_type="application/json",
                           REMOTE_ADDR="111.111.111.111")

    assert response.status_code == 204


def test_ok_signature_ip_in_network(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["111.111.111.0/24"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url, json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.112")

    assert response.status_code == 204


def test_ok_signature_invalid_network(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["131.103.20.160/27;165.254.145.0/26;104.192.143.0/24"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = json.dumps({"push": {"changes": [{"new": {"target": { "message": "test message"}}}]}})
    response = client.post(url,
                           data,
                           content_type="application/json",
                           HTTP_X_EVENT_KEY="repo:push",
                           REMOTE_ADDR="104.192.143.193")

    assert response.status_code == 400
    assert "Bad signature" in response.data["_error_message"]



def test_blocked_project(client):
    project = f.ProjectFactory(blocked_code=project_choices.BLOCKED_BY_STAFF)
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["111.111.111.111"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.111")

    assert response.status_code == 451


def test_invalid_ip(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["111.111.111.111"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.112")

    assert response.status_code == 400


def test_invalid_origin_ip_settings(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["testing"]
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.112")

    assert response.status_code == 400


def test_valid_local_network_ip(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": ["192.168.1.1"],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="192.168.1.1")

    assert response.status_code == 204


def test_not_ip_filter(client):
    project = f.ProjectFactory()
    f.ProjectModulesConfigFactory(project=project, config={
        "gitlab": {
            "secret": "tpnIwJDz4e",
            "valid_origin_ips": [],
        }
    })

    url = reverse("gitlab-hook-list")
    url = "{}?project={}&key={}".format(url, project.id, "tpnIwJDz4e")
    data = {"test:": "data"}
    response = client.post(url,
                           json.dumps(data),
                           content_type="application/json",
                           REMOTE_ADDR="111.111.111.111")

    assert response.status_code == 204


def test_push_event_detected(client):
    project = f.ProjectFactory()
    url = reverse("gitlab-hook-list")
    url = "%s?project=%s" % (url, project.id)
    data = deepcopy(push_base_payload)
    data["commits"] = [{
        "message": "test message",
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    data["total_commits_count"] = 1

    GitLabViewSet._validate_signature = mock.Mock(return_value=True)

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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
           test   TG-%s    #%s   ok
           bye!
        """ % (epic.ref, new_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
           test   TG-%s    #%s   ok
           bye!
        """ % (issue.ref, new_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s    #%s   ok
            bye!
        """ % (task.ref, new_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s    #%s   ok
            bye!
        """ % (user_story.ref, new_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1

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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s   ok
            bye!
        """ % (issue.ref),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s   ok
            bye!
        """ % (task.ref),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s   ok
            bye!
        """ % (user_story.ref),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]

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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s    #%s   ok
            test   TG-%s    #%s   ok
            bye!
        """ % (issue1.ref, new_status.slug, issue2.ref, new_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
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
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   tg-%s    #%s   ok
            bye!
        """ % (task.ref, new_status.slug.upper()),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
    mail.outbox = []
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id
    assert len(mail.outbox) == 1


def test_push_event_task_bad_processing_non_existing_ref(client):
    issue_status = f.IssueStatusFactory()
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-6666666    #%s   ok
            bye!
        """ % (issue_status.slug),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1
    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(issue_status.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The referenced element doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_us_bad_processing_non_existing_status(client):
    user_story = f.UserStoryFactory.create()
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s    #non-existing-slug   ok
            bye!
        """ % (user_story.ref),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1

    mail.outbox = []

    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"
    assert len(mail.outbox) == 0


def test_push_event_bad_processing_non_existing_status(client):
    issue = f.IssueFactory.create()
    payload = deepcopy(push_base_payload)
    payload["commits"] = [{
        "message": """test message
            test   TG-%s    #non-existing-slug   ok
            bye!
        """ % (issue.ref),
        "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
        "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
    }]
    payload["total_commits_count"] = 1

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
    Membership.objects.create(user=issue.owner, project=issue.project, role=f.RoleFactory.create(project=issue.project), is_admin=True)
    notify_policy = NotifyPolicy.objects.get(user=issue.owner, project=issue.project)
    notify_policy.notify_level = NotifyLevel.all
    notify_policy.save()

    payload = deepcopy(new_issue_base_payload)
    payload["object_attributes"]["title"] = "test-title"
    payload["object_attributes"]["description"] = "test-body"
    payload["object_attributes"]["url"] = "http://gitlab.com/test/project/issues/11"
    payload["object_attributes"]["action"] = "open"
    payload["repository"]["homepage"] = "test"

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

    payload = deepcopy(new_issue_base_payload)
    payload["object_attributes"]["title"] = "test-title"
    payload["object_attributes"]["description"] = "test-body"
    payload["object_attributes"]["url"] = "http://gitlab.com/test/project/issues/11"
    payload["object_attributes"]["action"] = "update"
    payload["repository"]["homepage"] = "test"

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

    payload = deepcopy(new_issue_base_payload)
    del payload["object_attributes"]["title"]
    del payload["object_attributes"]["description"]
    del payload["object_attributes"]["url"]
    payload["object_attributes"]["action"] = "open"
    payload["repository"]["homepage"] = "test"
    mail.outbox = []

    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)

    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "Invalid issue information"

    assert Issue.objects.count() == 1
    assert len(mail.outbox) == 0


def test_issue_comment_event_on_existing_issue_task_and_us(client):
    project = f.ProjectFactory()
    role = f.RoleFactory(project=project, permissions=["view_tasks", "view_issues", "view_us"])
    f.MembershipFactory(project=project, role=role, user=project.owner)
    user = f.UserFactory()

    issue = f.IssueFactory.create(external_reference=["gitlab", "http://gitlab.com/test/project/issues/11"], owner=project.owner, project=project)
    take_snapshot(issue, user=user)
    task = f.TaskFactory.create(external_reference=["gitlab", "http://gitlab.com/test/project/issues/11"], owner=project.owner, project=project)
    take_snapshot(task, user=user)
    us = f.UserStoryFactory.create(external_reference=["gitlab", "http://gitlab.com/test/project/issues/11"], owner=project.owner, project=project)
    take_snapshot(us, user=user)

    payload = deepcopy(issue_comment_base_payload)
    payload["user"]["username"] = "test"
    payload["issue"]["iid"] = "11"
    payload["issue"]["title"] = "test-title"
    payload["object_attributes"]["noteable_type"] = "Issue"
    payload["object_attributes"]["note"] = "Test body"
    payload["repository"]["homepage"] = "http://gitlab.com/test/project"

    mail.outbox = []

    assert get_history_queryset_by_model_instance(issue).count() == 0
    assert get_history_queryset_by_model_instance(task).count() == 0
    assert get_history_queryset_by_model_instance(us).count() == 0

    ev_hook = event_hooks.IssueCommentEventHook(issue.project, payload)
    ev_hook.process_event()

    issue_history = get_history_queryset_by_model_instance(issue)
    assert issue_history.count() == 1
    assert "Test body" in issue_history[0].comment

    task_history = get_history_queryset_by_model_instance(task)
    assert task_history.count() == 1
    assert "Test body" in issue_history[0].comment

    us_history = get_history_queryset_by_model_instance(us)
    assert us_history.count() == 1
    assert "Test body" in issue_history[0].comment

    assert len(mail.outbox) == 3


def test_issue_comment_event_on_not_existing_issue_task_and_us(client):
    issue = f.IssueFactory.create(external_reference=["gitlab", "10"])
    take_snapshot(issue, user=issue.owner)
    task = f.TaskFactory.create(project=issue.project, external_reference=["gitlab", "10"])
    take_snapshot(task, user=task.owner)
    us = f.UserStoryFactory.create(project=issue.project, external_reference=["gitlab", "10"])
    take_snapshot(us, user=us.owner)

    payload = deepcopy(issue_comment_base_payload)
    payload["user"]["username"] = "test"
    payload["issue"]["iid"] = "99999"
    payload["issue"]["title"] = "test-title"
    payload["object_attributes"]["noteable_type"] = "Issue"
    payload["object_attributes"]["note"] = "test comment"
    payload["repository"]["homepage"] = "test"

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
    issue = f.IssueFactory.create(external_reference=["gitlab", "10"])
    take_snapshot(issue, user=issue.owner)

    payload = deepcopy(issue_comment_base_payload)
    payload["user"]["username"] = "test"
    payload["issue"]["iid"] = "10"
    payload["issue"]["title"] = "test-title"
    payload["object_attributes"]["noteable_type"] = "Issue"
    del payload["object_attributes"]["note"]
    payload["repository"]["homepage"] = "test"

    ev_hook = event_hooks.IssueCommentEventHook(issue.project, payload)

    mail.outbox = []

    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "Invalid issue comment information"

    assert Issue.objects.count() == 1
    assert len(mail.outbox) == 0


def test_api_get_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 200
    content = response.data
    assert "gitlab" in content
    assert content["gitlab"]["secret"] != ""
    assert content["gitlab"]["webhooks_url"] != ""


def test_api_patch_project_modules(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("projects-modules", args=(project.id,))

    client.login(project.owner)
    data = {
        "gitlab": {
            "secret": "test_secret",
            "url": "test_url",
        }
    }
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 204

    config = services.get_modules_config(project).config
    assert "gitlab" in config
    assert config["gitlab"]["secret"] == "test_secret"
    assert config["gitlab"]["webhooks_url"] != "test_url"


def test_replace_gitlab_references():
    ev_hook = event_hooks.BaseGitLabEventHook
    assert ev_hook.replace_gitlab_references(None, "project-url", "#2") == "[GitLab#2](project-url/issues/2)"
    assert ev_hook.replace_gitlab_references(None, "project-url", "#2 ") == "[GitLab#2](project-url/issues/2) "
    assert ev_hook.replace_gitlab_references(None, "project-url", " #2 ") == " [GitLab#2](project-url/issues/2) "
    assert ev_hook.replace_gitlab_references(None, "project-url", " #2") == " [GitLab#2](project-url/issues/2)"
    assert ev_hook.replace_gitlab_references(None, "project-url", "#test") == "#test"
    assert ev_hook.replace_gitlab_references(None, "project-url", None) == ""
