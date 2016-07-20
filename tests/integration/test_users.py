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
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files import File

from .. import factories as f
from ..utils import DUMMY_BMP_DATA

from taiga.base.utils import json
from taiga.base.utils.thumbnails import get_thumbnail_url
from taiga.base.utils.dicts import into_namedtuple
from taiga.users import models
from taiga.users.serializers import LikedObjectSerializer, VotedObjectSerializer
from taiga.auth.tokens import get_token_for_user
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects import choices as project_choices
from taiga.users.services import get_watched_list, get_voted_list, get_liked_list
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.notifications.models import NotifyPolicy

from easy_thumbnails.files import generate_all_aliases, get_thumbnailer

import os

pytestmark = pytest.mark.django_db


def test_users_create_through_standard_api(client):
    user = f.UserFactory.create(is_superuser=True)

    url = reverse('users-list')
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 405

    client.login(user)

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 405


def test_update_user_with_same_email(client):
    user = f.UserFactory.create(email="same@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "same@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_update_user_with_duplicated_email(client):
    f.UserFactory.create(email="one@email.com")
    user = f.UserFactory.create(email="two@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "one@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_update_user_with_invalid_email(client):
    user = f.UserFactory.create(email="my@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "my@email"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Not valid email'


def test_update_user_with_unallowed_domain_email(client, settings):
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']
    user = f.UserFactory.create(email="my@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "my@invalid-email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Not valid email'


def test_update_user_with_allowed_domain_email(client, settings):
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']

    user = f.UserFactory.create(email="old@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "new@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is not None
    assert user.new_email == "new@email.com"


def test_update_user_with_valid_email(client):
    user = f.UserFactory.create(email="old@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "new@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is not None
    assert user.new_email == "new@email.com"


def test_validate_requested_email_change(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "change_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is None
    assert user.new_email is None
    assert user.email == "new@email.com"

def test_validate_requested_email_change_for_anonymous_user(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "change_email_token"}

    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is None
    assert user.new_email is None
    assert user.email == "new@email.com"

def test_validate_requested_email_change_without_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400


def test_validate_requested_email_change_with_invalid_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "invalid_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400


def test_delete_self_user(client):
    user = f.UserFactory.create()
    url = reverse('users-detail', kwargs={"pk": user.pk})

    client.login(user)
    response = client.delete(url)

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.full_name == "Deleted user"


def test_delete_self_user_blocking_projects(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    url = reverse('users-detail', kwargs={"pk": user.pk})

    assert project.blocked_code == None
    client.login(user)
    response = client.delete(url)
    project = user.owned_projects.first()
    assert project.blocked_code == project_choices.BLOCKED_BY_OWNER_LEAVING


def test_delete_self_user_remove_membership_projects(client):
    project = f.ProjectFactory.create()
    user = f.UserFactory.create()
    f.create_membership(project=project, user=user)

    url = reverse('users-detail', kwargs={"pk": user.pk})

    assert project.memberships.all().count() == 1

    client.login(user)
    response = client.delete(url)

    assert project.memberships.all().count() == 0


def test_cancel_self_user_with_valid_token(client):
    user = f.UserFactory.create()
    url = reverse('users-cancel')
    cancel_token = get_token_for_user(user, "cancel_account")
    data = {"cancel_token": cancel_token}
    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.full_name == "Deleted user"


def test_cancel_self_user_with_invalid_token(client):
    user = f.UserFactory.create()
    url = reverse('users-cancel')
    data = {"cancel_token": "invalid_cancel_token"}
    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400


def test_change_avatar(client):
    url = reverse('users-change-avatar')

    user = f.UserFactory()
    client.login(user)

    with NamedTemporaryFile() as avatar:
        # Test no avatar send
        post_data = {}
        response = client.post(url, post_data)
        assert response.status_code == 400

        # Test invalid file send
        post_data = {
            'avatar': avatar
        }
        response = client.post(url, post_data)
        assert response.status_code == 400

        # Test empty valid avatar send
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)
        response = client.post(url, post_data)
        assert response.status_code == 200


def test_change_avatar_with_long_file_name(client):
    url = reverse('users-change-avatar')
    user = f.UserFactory()

    with NamedTemporaryFile(delete=False) as avatar:
        avatar.name=500*"x"+".bmp"
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)

        client.login(user)
        post_data = {'avatar': avatar}
        response = client.post(url, post_data)

        assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_change_avatar_removes_the_old_one(client):
    url = reverse('users-change-avatar')
    user = f.UserFactory()

    with NamedTemporaryFile(delete=False) as avatar:
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)
        user.photo = File(avatar)
        user.save()
        generate_all_aliases(user.photo, include_global=True)

    with NamedTemporaryFile(delete=False) as avatar:
        thumbnailer = get_thumbnailer(user.photo)
        original_photo_paths = [user.photo.path]
        original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]
        assert all(list(map(os.path.exists, original_photo_paths)))

        client.login(user)
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)
        post_data = {'avatar': avatar}
        response = client.post(url, post_data)

        assert response.status_code == 200
        assert not any(list(map(os.path.exists, original_photo_paths)))


@pytest.mark.django_db(transaction=True)
def test_remove_avatar(client):
    url = reverse('users-remove-avatar')
    user = f.UserFactory()

    with NamedTemporaryFile(delete=False) as avatar:
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)
        user.photo = File(avatar)
        user.save()
        generate_all_aliases(user.photo, include_global=True)

    thumbnailer = get_thumbnailer(user.photo)
    original_photo_paths = [user.photo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]
    assert all(list(map(os.path.exists, original_photo_paths)))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200
    assert not any(list(map(os.path.exists, original_photo_paths)))


def test_list_contacts_private_projects(client):
    project = f.ProjectFactory.create()
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role = f.RoleFactory(project=project, permissions=["view_project"])
    membership_1 = f.MembershipFactory.create(project=project, user=user_1, role=role)
    membership_2 = f.MembershipFactory.create(project=project, user=user_2, role=role)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_content = response.data
    assert len(response_content) == 0

    client.login(user_1)
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_content = response.data
    assert len(response_content) == 1
    assert response_content[0]["id"] == user_2.id


def test_list_contacts_no_projects(client):
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role_1 = f.RoleFactory(permissions=["view_project"])
    role_2 = f.RoleFactory(permissions=["view_project"])
    membership_1 = f.MembershipFactory.create(project=role_1.project, user=user_1, role=role_1)
    membership_2 = f.MembershipFactory.create(project=role_2.project, user=user_2, role=role_2)

    client.login(user_1)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200

    response_content = response.data
    assert len(response_content) == 0


def test_list_contacts_public_projects(client):
    project = f.ProjectFactory.create(is_private=False,
            anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
            public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)))

    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role = f.RoleFactory(project=project)
    membership_1 = f.MembershipFactory.create(project=project, user=user_1, role=role)
    membership_2 = f.MembershipFactory.create(project=project, user=user_2, role=role)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200

    response_content = response.data
    assert len(response_content) == 1
    assert response_content[0]["id"] == user_2.id


def test_mail_permissions(client):
    user_1 = f.UserFactory.create(is_superuser=True)
    user_2 = f.UserFactory.create()

    url1 = reverse('users-detail', kwargs={"pk": user_1.pk})
    url2 = reverse('users-detail', kwargs={"pk": user_2.pk})

    # Anonymous user
    response = client.json.get(url1)
    assert response.status_code == 200
    assert "email" not in response.data

    response = client.json.get(url2)
    assert response.status_code == 200
    assert "email" not in response.data

    # Superuser
    client.login(user_1)

    response = client.json.get(url1)
    assert response.status_code == 200
    assert "email" in response.data

    response = client.json.get(url2)
    assert response.status_code == 200
    assert "email" in response.data

    # Normal user
    client.login(user_2)

    response = client.json.get(url1)
    assert response.status_code == 200
    assert "email" not in response.data

    response = client.json.get(url2)
    assert response.status_code == 200
    assert "email" in response.data


def test_get_watched_list():
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)
    project.add_watcher(fav_user)

    user_story = f.UserStoryFactory(project=project, subject="Testing user story")
    user_story.add_watcher(fav_user)

    task = f.TaskFactory(project=project, subject="Testing task")
    task.add_watcher(fav_user)

    issue = f.IssueFactory(project=project, subject="Testing issue")
    issue.add_watcher(fav_user)

    assert len(get_watched_list(fav_user, viewer_user)) == 4
    assert len(get_watched_list(fav_user, viewer_user, type="project")) == 1
    assert len(get_watched_list(fav_user, viewer_user, type="userstory")) == 1
    assert len(get_watched_list(fav_user, viewer_user, type="task")) == 1
    assert len(get_watched_list(fav_user, viewer_user, type="issue")) == 1
    assert len(get_watched_list(fav_user, viewer_user, type="unknown")) == 0

    assert len(get_watched_list(fav_user, viewer_user, q="issue")) == 1
    assert len(get_watched_list(fav_user, viewer_user, q="unexisting text")) == 0


def test_get_liked_list():
    fan_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fan_user)
    content_type = ContentType.objects.get_for_model(project)
    f.LikeFactory(content_type=content_type, object_id=project.id, user=fan_user)

    assert len(get_liked_list(fan_user, viewer_user)) == 1
    assert len(get_liked_list(fan_user, viewer_user, type="project")) == 1
    assert len(get_liked_list(fan_user, viewer_user, type="unknown")) == 0

    assert len(get_liked_list(fan_user, viewer_user, q="project")) == 1
    assert len(get_liked_list(fan_user, viewer_user, q="unexisting text")) == 0


def test_get_voted_list():
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)

    user_story = f.UserStoryFactory(project=project, subject="Testing user story")
    content_type = ContentType.objects.get_for_model(user_story)
    f.VoteFactory(content_type=content_type, object_id=user_story.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=user_story.id, count=1)

    task = f.TaskFactory(project=project, subject="Testing task")
    content_type = ContentType.objects.get_for_model(task)
    f.VoteFactory(content_type=content_type, object_id=task.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=task.id, count=1)

    issue = f.IssueFactory(project=project, subject="Testing issue")
    content_type = ContentType.objects.get_for_model(issue)
    f.VoteFactory(content_type=content_type, object_id=issue.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=issue.id, count=1)

    assert len(get_voted_list(fav_user, viewer_user)) == 3
    assert len(get_voted_list(fav_user, viewer_user, type="userstory")) == 1
    assert len(get_voted_list(fav_user, viewer_user, type="task")) == 1
    assert len(get_voted_list(fav_user, viewer_user, type="issue")) == 1
    assert len(get_voted_list(fav_user, viewer_user, type="unknown")) == 0

    assert len(get_voted_list(fav_user, viewer_user, q="issue")) == 1
    assert len(get_voted_list(fav_user, viewer_user, q="unexisting text")) == 0


def test_get_watched_list_valid_info_for_project():
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    project.add_watcher(fav_user)

    raw_project_watch_info = get_watched_list(fav_user, viewer_user)[0]

    project_watch_info = LikedObjectSerializer(into_namedtuple(raw_project_watch_info)).data

    assert project_watch_info["type"] == "project"
    assert project_watch_info["id"] == project.id
    assert project_watch_info["ref"] == None
    assert project_watch_info["slug"] == project.slug
    assert project_watch_info["name"] == project.name
    assert project_watch_info["subject"] == None
    assert project_watch_info["description"] == project.description
    assert project_watch_info["assigned_to"] == None
    assert project_watch_info["status"] == None
    assert project_watch_info["status_color"] == None
    assert project_watch_info["is_private"] == project.is_private
    assert project_watch_info["logo_small_url"] ==  get_thumbnail_url(project.logo, settings.THN_LOGO_SMALL)
    assert project_watch_info["is_fan"] == False
    assert project_watch_info["is_watcher"] == False
    assert project_watch_info["total_watchers"] == 1
    assert project_watch_info["total_fans"] == 0
    assert project_watch_info["project"] == None
    assert project_watch_info["project_name"] == None
    assert project_watch_info["project_slug"] == None
    assert project_watch_info["project_is_private"] == None
    assert project_watch_info["project_blocked_code"] == None
    assert project_watch_info["assigned_to"] == None
    assert project_watch_info["assigned_to_extra_info"] == None


def test_get_watched_list_for_project_with_ignored_notify_level():
    #If the notify policy level is ignore the project shouldn't be in the watched results
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project", tags=['test', 'tag'])
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)
    notify_policy = NotifyPolicy.objects.get(user=fav_user, project=project)
    notify_policy.notify_level=NotifyLevel.none
    notify_policy.save()

    watched_list = get_watched_list(fav_user, viewer_user)
    assert len(watched_list) == 0


def test_get_liked_list_valid_info():
    fan_user = f.UserFactory()
    viewer_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    content_type = ContentType.objects.get_for_model(project)
    like = f.LikeFactory(content_type=content_type, object_id=project.id, user=fan_user)
    project.refresh_totals()

    raw_project_like_info = get_liked_list(fan_user, viewer_user)[0]
    project_like_info = LikedObjectSerializer(into_namedtuple(raw_project_like_info)).data

    assert project_like_info["type"] == "project"
    assert project_like_info["id"] == project.id
    assert project_like_info["ref"] == None
    assert project_like_info["slug"] == project.slug
    assert project_like_info["name"] == project.name
    assert project_like_info["subject"] == None
    assert project_like_info["description"] == project.description
    assert project_like_info["assigned_to"] == None
    assert project_like_info["status"] == None
    assert project_like_info["status_color"] == None
    assert project_like_info["is_private"] == project.is_private
    assert project_like_info["logo_small_url"] ==  get_thumbnail_url(project.logo, settings.THN_LOGO_SMALL)

    assert project_like_info["is_fan"] == False
    assert project_like_info["is_watcher"] == False
    assert project_like_info["total_watchers"] == 0
    assert project_like_info["total_fans"] == 1
    assert project_like_info["project"] == None
    assert project_like_info["project_name"] == None
    assert project_like_info["project_slug"] == None
    assert project_like_info["project_is_private"] == None
    assert project_like_info["project_blocked_code"] == None
    assert project_like_info["assigned_to"] == None
    assert project_like_info["assigned_to_extra_info"] == None


def test_get_watched_list_valid_info_for_not_project_types():
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()
    assigned_to_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")

    factories = {
        "userstory": f.UserStoryFactory,
        "task": f.TaskFactory,
        "issue": f.IssueFactory
    }

    for object_type in factories:
        instance = factories[object_type](project=project,
            subject="Testing",
            tags=["test1", "test2"],
            assigned_to=assigned_to_user)

        instance.add_watcher(fav_user)
        raw_instance_watch_info = get_watched_list(fav_user, viewer_user, type=object_type)[0]
        instance_watch_info = VotedObjectSerializer(into_namedtuple(raw_instance_watch_info)).data

        assert instance_watch_info["type"] == object_type
        assert instance_watch_info["id"] == instance.id
        assert instance_watch_info["ref"] == instance.ref
        assert instance_watch_info["slug"] == None
        assert instance_watch_info["name"] == None
        assert instance_watch_info["subject"] == instance.subject
        assert instance_watch_info["description"] == None
        assert instance_watch_info["assigned_to"] == instance.assigned_to.id
        assert instance_watch_info["status"] == instance.status.name
        assert instance_watch_info["status_color"] == instance.status.color

        tags_colors = {tc["name"]:tc["color"] for tc in instance_watch_info["tags_colors"]}
        assert "test1" in tags_colors
        assert "test2" in tags_colors

        assert instance_watch_info["is_private"] == None
        assert instance_watch_info["logo_small_url"] ==  None
        assert instance_watch_info["is_voter"] == False
        assert instance_watch_info["is_watcher"] == False
        assert instance_watch_info["total_watchers"] == 1
        assert instance_watch_info["total_voters"] == 0
        assert instance_watch_info["project"] == instance.project.id
        assert instance_watch_info["project_name"] == instance.project.name
        assert instance_watch_info["project_slug"] == instance.project.slug
        assert instance_watch_info["project_is_private"] == instance.project.is_private
        assert instance_watch_info["project_blocked_code"] == instance.project.blocked_code
        assert instance_watch_info["assigned_to"] != None
        assert instance_watch_info["assigned_to_extra_info"]["username"] == instance.assigned_to.username
        assert instance_watch_info["assigned_to_extra_info"]["full_name_display"] == instance.assigned_to.get_full_name()
        assert instance_watch_info["assigned_to_extra_info"]["photo"] == None
        assert instance_watch_info["assigned_to_extra_info"]["gravatar_id"] != None


def test_get_voted_list_valid_info():
    fav_user = f.UserFactory()
    viewer_user = f.UserFactory()
    assigned_to_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")

    factories = {
        "userstory": f.UserStoryFactory,
        "task": f.TaskFactory,
        "issue": f.IssueFactory
    }

    for object_type in factories:
        instance = factories[object_type](project=project,
            subject="Testing",
            tags=["test1", "test2"],
            assigned_to=assigned_to_user)

        content_type = ContentType.objects.get_for_model(instance)
        vote = f.VoteFactory(content_type=content_type, object_id=instance.id, user=fav_user)
        f.VotesFactory(content_type=content_type, object_id=instance.id, count=3)

        raw_instance_vote_info = get_voted_list(fav_user, viewer_user, type=object_type)[0]
        instance_vote_info = VotedObjectSerializer(into_namedtuple(raw_instance_vote_info)).data

        assert instance_vote_info["type"] == object_type
        assert instance_vote_info["id"] == instance.id
        assert instance_vote_info["ref"] == instance.ref
        assert instance_vote_info["slug"] == None
        assert instance_vote_info["name"] == None
        assert instance_vote_info["subject"] == instance.subject
        assert instance_vote_info["description"] == None
        assert instance_vote_info["assigned_to"] == instance.assigned_to.id
        assert instance_vote_info["status"] == instance.status.name
        assert instance_vote_info["status_color"] == instance.status.color

        tags_colors = {tc["name"]:tc["color"] for tc in instance_vote_info["tags_colors"]}
        assert "test1" in tags_colors
        assert "test2" in tags_colors

        assert instance_vote_info["is_private"] == None
        assert instance_vote_info["logo_small_url"] ==  None
        assert instance_vote_info["is_voter"] == False
        assert instance_vote_info["is_watcher"] == False
        assert instance_vote_info["total_watchers"] == 0
        assert instance_vote_info["total_voters"] == 3
        assert instance_vote_info["project"] == instance.project.id
        assert instance_vote_info["project_name"] == instance.project.name
        assert instance_vote_info["project_slug"] == instance.project.slug
        assert instance_vote_info["project_is_private"] == instance.project.is_private
        assert instance_vote_info["project_blocked_code"] == instance.project.blocked_code
        assert instance_vote_info["assigned_to"] != None
        assert instance_vote_info["assigned_to_extra_info"]["username"] == instance.assigned_to.username
        assert instance_vote_info["assigned_to_extra_info"]["full_name_display"] == instance.assigned_to.get_full_name()
        assert instance_vote_info["assigned_to_extra_info"]["photo"] == None
        assert instance_vote_info["assigned_to_extra_info"]["gravatar_id"] != None



def test_get_watched_list_with_liked_and_voted_objects(client):
    fav_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)
    project.add_watcher(fav_user)
    content_type = ContentType.objects.get_for_model(project)
    f.LikeFactory(content_type=content_type, object_id=project.id, user=fav_user)

    voted_elements_factories = {
        "userstory": f.UserStoryFactory,
        "task": f.TaskFactory,
        "issue": f.IssueFactory
    }

    for object_type in voted_elements_factories:
        instance = voted_elements_factories[object_type](project=project)
        content_type = ContentType.objects.get_for_model(instance)
        instance.add_watcher(fav_user)
        f.VoteFactory(content_type=content_type, object_id=instance.id, user=fav_user)

    client.login(fav_user)
    url = reverse('users-watched', kwargs={"pk": fav_user.pk})
    response = client.get(url, content_type="application/json")

    for element_data in response.data:
        #assert element_data["is_watcher"] == True
        if element_data["type"] == "project":
            assert element_data["is_fan"] == True
        else:
            assert element_data["is_voter"] == True


def test_get_liked_list_with_watched_objects(client):
    fav_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)
    project.add_watcher(fav_user)
    content_type = ContentType.objects.get_for_model(project)
    f.LikeFactory(content_type=content_type, object_id=project.id, user=fav_user)

    client.login(fav_user)
    url = reverse('users-liked', kwargs={"pk": fav_user.pk})
    response = client.get(url, content_type="application/json")

    element_data  = response.data[0]
    assert element_data["is_watcher"] == True
    assert element_data["is_fan"] == True


def test_get_voted_list_with_watched_objects(client):
    fav_user = f.UserFactory()

    project = f.ProjectFactory(is_private=False, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=fav_user)

    voted_elements_factories = {
        "userstory": f.UserStoryFactory,
        "task": f.TaskFactory,
        "issue": f.IssueFactory
    }

    for object_type in voted_elements_factories:
        instance = voted_elements_factories[object_type](project=project)
        content_type = ContentType.objects.get_for_model(instance)
        instance.add_watcher(fav_user)
        f.VoteFactory(content_type=content_type, object_id=instance.id, user=fav_user)

    client.login(fav_user)
    url = reverse('users-voted', kwargs={"pk": fav_user.pk})
    response = client.get(url, content_type="application/json")

    for element_data in response.data:
        assert element_data["is_watcher"] == True
        assert element_data["is_voter"] == True


def test_get_watched_list_permissions():
    fav_user = f.UserFactory()
    viewer_unpriviliged_user = f.UserFactory()
    viewer_priviliged_user = f.UserFactory()

    project = f.ProjectFactory(is_private=True, name="Testing project")
    project.add_watcher(fav_user)
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=viewer_priviliged_user)

    user_story = f.UserStoryFactory(project=project, subject="Testing user story")
    user_story.add_watcher(fav_user)

    task = f.TaskFactory(project=project, subject="Testing task")
    task.add_watcher(fav_user)

    issue = f.IssueFactory(project=project, subject="Testing issue")
    issue.add_watcher(fav_user)

    #If the project is private a viewer user without any permission shouldn' see
    # any vote
    assert len(get_watched_list(fav_user, viewer_unpriviliged_user)) == 0

    #If the project is private but the viewer user has permissions the votes should
    # be accesible
    assert len(get_watched_list(fav_user, viewer_priviliged_user)) == 4

    #If the project is private but has the required anon permissions the votes should
    # be accesible by any user too
    project.anon_permissions = ["view_project", "view_us", "view_tasks", "view_issues"]
    project.save()
    assert len(get_watched_list(fav_user, viewer_unpriviliged_user)) == 4


def test_get_liked_list_permissions():
    fan_user = f.UserFactory()
    viewer_unpriviliged_user = f.UserFactory()
    viewer_priviliged_user = f.UserFactory()

    project = f.ProjectFactory(is_private=True, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=viewer_priviliged_user)
    content_type = ContentType.objects.get_for_model(project)
    f.LikeFactory(content_type=content_type, object_id=project.id, user=fan_user)

    #If the project is private a viewer user without any permission shouldn' see
    # any vote
    assert len(get_liked_list(fan_user, viewer_unpriviliged_user)) == 0

    #If the project is private but the viewer user has permissions the votes should
    # be accesible
    assert len(get_liked_list(fan_user, viewer_priviliged_user)) == 1

    #If the project is private but has the required anon permissions the votes should
    # be accesible by any user too
    project.anon_permissions = ["view_project", "view_us", "view_tasks", "view_issues"]
    project.save()
    assert len(get_liked_list(fan_user, viewer_unpriviliged_user)) == 1


def test_get_voted_list_permissions():
    fav_user = f.UserFactory()
    viewer_unpriviliged_user = f.UserFactory()
    viewer_priviliged_user = f.UserFactory()

    project = f.ProjectFactory(is_private=True, name="Testing project")
    role = f.RoleFactory(project=project, permissions=["view_project", "view_us", "view_tasks", "view_issues"])
    membership = f.MembershipFactory(project=project, role=role, user=viewer_priviliged_user)

    user_story = f.UserStoryFactory(project=project, subject="Testing user story")
    content_type = ContentType.objects.get_for_model(user_story)
    f.VoteFactory(content_type=content_type, object_id=user_story.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=user_story.id, count=1)

    task = f.TaskFactory(project=project, subject="Testing task")
    content_type = ContentType.objects.get_for_model(task)
    f.VoteFactory(content_type=content_type, object_id=task.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=task.id, count=1)

    issue = f.IssueFactory(project=project, subject="Testing issue")
    content_type = ContentType.objects.get_for_model(issue)
    f.VoteFactory(content_type=content_type, object_id=issue.id, user=fav_user)
    f.VotesFactory(content_type=content_type, object_id=issue.id, count=1)

    #If the project is private a viewer user without any permission shouldn' see
    # any vote
    assert len(get_voted_list(fav_user, viewer_unpriviliged_user)) == 0

    #If the project is private but the viewer user has permissions the votes should
    # be accesible
    assert len(get_voted_list(fav_user, viewer_priviliged_user)) == 3

    #If the project is private but has the required anon permissions the votes should
    # be accesible by any user too
    project.anon_permissions = ["view_project", "view_us", "view_tasks", "view_issues"]
    project.save()
    assert len(get_voted_list(fav_user, viewer_unpriviliged_user)) == 3
