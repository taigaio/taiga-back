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

from unittest import mock
from django.core.urlresolvers import reverse

from taiga.projects import services
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_members_from_bulk():
    data = [{"role_id": "1", "email": "member1@email.com"},
            {"role_id": "1", "email": "member2@email.com"}]
    members = services.get_members_from_bulk(data, project_id=1)

    assert len(members) == 2
    assert members[0].email == "member1@email.com"
    assert members[1].email == "member2@email.com"


def test_create_members_in_bulk():
    with mock.patch("taiga.projects.services.members.db") as db:
        data = [{"role_id": "1", "email": "member1@email.com"},
                {"role_id": "1", "email": "member2@email.com"}]
        members = services.create_members_in_bulk(data, project_id=1)
        db.save_in_bulk.assert_called_once_with(members, None, None)


def test_api_create_bulk_members(client):
    project = f.ProjectFactory()
    john = f.UserFactory.create()
    joseph = f.UserFactory.create()
    tester = f.RoleFactory(project=project, name="Tester")
    gamer = f.RoleFactory(project=project, name="Gamer")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": john.email},
            {"role_id": gamer.pk, "email": joseph.email},
        ]
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data[0]["email"] == john.email
    assert response.data[1]["email"] == joseph.email


def test_api_create_bulk_members_with_invalid_roles(client):
    project = f.ProjectFactory()
    john = f.UserFactory.create()
    joseph = f.UserFactory.create()
    tester = f.RoleFactory(name="Tester")
    gamer = f.RoleFactory(name="Gamer")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": john.email},
            {"role_id": gamer.pk, "email": joseph.email},
        ]
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "bulk_memberships" in response.data


def test_api_create_bulk_members_with_allowed_domain(client):
    project = f.ProjectFactory()
    john = f.UserFactory.create()
    joseph = f.UserFactory.create()
    tester = f.RoleFactory(project=project, name="Tester")
    gamer = f.RoleFactory(project=project, name="Gamer")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": "test1@email.com"},
            {"role_id": gamer.pk, "email": "test2@email.com"},
        ]
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data[0]["email"] == "test1@email.com"
    assert response.data[1]["email"] == "test2@email.com"


def test_api_create_bulk_members_with_allowed_and_unallowed_domain(client, settings):
    project = f.ProjectFactory()
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']
    tester = f.RoleFactory(project=project, name="Tester")
    gamer = f.RoleFactory(project=project, name="Gamer")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": "test@invalid-domain.com"},
            {"role_id": gamer.pk, "email": "test@email.com"},
        ]
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "email" in response.data["bulk_memberships"][0]
    assert "email" not in response.data["bulk_memberships"][1]


def test_api_create_bulk_members_with_unallowed_domains(client, settings):
    project = f.ProjectFactory()
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']
    tester = f.RoleFactory(project=project, name="Tester")
    gamer = f.RoleFactory(project=project, name="Gamer")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": "test1@invalid-domain.com"},
            {"role_id": gamer.pk, "email": "test2@invalid-domain.com"},
        ]
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "email" in response.data["bulk_memberships"][0]
    assert "email" in response.data["bulk_memberships"][1]


def test_api_create_bulk_members_without_enough_memberships_private_project_slots_one_project(client):
    user = f.UserFactory.create(max_memberships_private_projects=3)
    project = f.ProjectFactory(owner=user, is_private=True)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": role.pk, "email": "test1@test.com"},
            {"role_id": role.pk, "email": "test2@test.com"},
            {"role_id": role.pk, "email": "test3@test.com"},
            {"role_id": role.pk, "email": "test4@test.com"},
        ]
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "reached your current limit of memberships for private" in response.data["_error_message"]



def test_api_create_bulk_members_for_admin_without_enough_memberships_private_project_slots_one_project(client):
    owner = f.UserFactory.create(max_memberships_private_projects=3)
    user = f.UserFactory.create()
    project = f.ProjectFactory(owner=owner, is_private=True)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": role.pk, "email": "test1@test.com"},
            {"role_id": role.pk, "email": "test2@test.com"},
            {"role_id": role.pk, "email": "test3@test.com"},
            {"role_id": role.pk, "email": "test4@test.com"},
        ]
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "reached your current limit of memberships for private" in response.data["_error_message"]



def test_api_create_bulk_members_with_enough_memberships_private_project_slots_multiple_projects(client):
    user = f.UserFactory.create(max_memberships_private_projects=6)
    project = f.ProjectFactory(owner=user, is_private=True)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    other_project = f.ProjectFactory(owner=user)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": role.pk, "email": "test1@test.com"},
            {"role_id": role.pk, "email": "test2@test.com"},
            {"role_id": role.pk, "email": "test3@test.com"},
            {"role_id": role.pk, "email": "test4@test.com"},
        ]
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200


def test_api_create_bulk_members_without_enough_memberships_public_project_slots_one_project(client):
    user = f.UserFactory.create(max_memberships_public_projects=3)
    project = f.ProjectFactory(owner=user, is_private=False)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": role.pk, "email": "test1@test.com"},
            {"role_id": role.pk, "email": "test2@test.com"},
            {"role_id": role.pk, "email": "test3@test.com"},
            {"role_id": role.pk, "email": "test4@test.com"},
        ]
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "reached your current limit of memberships for public" in response.data["_error_message"]


def test_api_create_bulk_members_with_enough_memberships_public_project_slots_multiple_projects(client):
    user = f.UserFactory.create(max_memberships_public_projects=6)
    project = f.ProjectFactory(owner=user, is_private=False)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    other_project = f.ProjectFactory(owner=user)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)

    url = reverse("memberships-bulk-create")

    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": role.pk, "email": "test1@test.com"},
            {"role_id": role.pk, "email": "test2@test.com"},
            {"role_id": role.pk, "email": "test3@test.com"},
            {"role_id": role.pk, "email": "test4@test.com"},
        ]
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200


def test_api_create_bulk_members_with_extra_text(client, outbox):
    project = f.ProjectFactory()
    tester = f.RoleFactory(project=project, name="Tester")
    f.MembershipFactory(project=project, user=project.owner, is_admin=True)
    url = reverse("memberships-bulk-create")

    invitation_extra_text = "this is a not so random invitation text"
    data = {
        "project_id": project.id,
        "bulk_memberships": [
            {"role_id": tester.pk, "email": "john@email.com"},
        ],
        "invitation_extra_text": invitation_extra_text
    }
    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data[0]["email"] == "john@email.com"

    message = outbox[0]
    assert len(outbox) == 1
    assert message.to == ["john@email.com"]
    assert "this is a not so random invitation text" in message.body


def test_api_resend_invitation(client, outbox):
    invitation = f.create_invitation(user=None)
    f.MembershipFactory(project=invitation.project, user=invitation.project.owner, is_admin=True)
    url = reverse("memberships-resend-invitation", kwargs={"pk": invitation.pk})

    client.login(invitation.project.owner)
    response = client.post(url)

    assert response.status_code == 204
    assert len(outbox) == 1
    assert outbox[0].to == [invitation.email]


def test_api_invite_existing_user(client, outbox):
    "Should create the invitation linked to that user"
    user = f.UserFactory.create()
    role = f.RoleFactory.create()
    f.MembershipFactory(project=role.project, user=role.project.owner, is_admin=True)

    client.login(role.project.owner)

    url = reverse("memberships-list")
    data = {"role": role.pk, "project": role.project.pk, "email": user.email}

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201, response.data
    assert len(outbox) == 1
    assert user.memberships.count() == 1

    message = outbox[0]

    assert message.to == [user.email]
    assert "Added to the project" in message.subject


def test_api_create_invalid_membership_email_failing(client):
    "Should not create the invitation linked to that user"
    user = f.UserFactory.create()
    role = f.RoleFactory.create()
    client.login(role.project.owner)

    url = reverse("memberships-list")
    data = {"role": role.pk, "project": role.project.pk}

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400, response.data
    assert user.memberships.count() == 0


def test_api_create_invalid_membership_role_doesnt_exist_in_the_project(client):
    "Should not create the invitation linked to that user"
    user = f.UserFactory.create()
    role = f.RoleFactory.create()
    project = f.ProjectFactory.create()

    client.login(project.owner)

    url = reverse("memberships-list")
    data = {"role": role.pk, "project": project.pk, "email": user.email}

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400, response.data
    assert response.data["role"][0] == "Invalid role for the project"
    assert user.memberships.count() == 0


def test_api_create_membership(client):
    membership = f.MembershipFactory(is_admin=True)
    role = f.RoleFactory.create(project=membership.project)
    user = f.UserFactory.create()

    client.login(membership.user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": role.project.pk, "email": user.email}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert response.data["user_email"] == user.email


def test_api_create_membership_with_unallowed_domain(client, settings):
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']

    membership = f.MembershipFactory(is_admin=True)
    role = f.RoleFactory.create(project=membership.project)

    client.login(membership.user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": role.project.pk, "email": "test@invalid-email.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "email" in response.data


def test_api_create_membership_with_allowed_domain(client, settings):
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']

    membership = f.MembershipFactory(is_admin=True)
    role = f.RoleFactory.create(project=membership.project)

    client.login(membership.user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": role.project.pk, "email": "test@email.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert response.data["email"] == "test@email.com"


def test_api_create_membership_without_enough_memberships_private_project_slots_one_projects(client):
    user = f.UserFactory.create(max_memberships_private_projects=1)
    project = f.ProjectFactory(owner=user, is_private=True)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    client.login(user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": project.pk, "email": "test@test.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "reached your current limit of memberships for private" in response.data["_error_message"]


def test_api_create_membership_with_enough_memberships_private_project_slots_multiple_projects(client):
    user = f.UserFactory.create(max_memberships_private_projects=5)
    project = f.ProjectFactory(owner=user, is_private=True)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    other_project = f.ProjectFactory(owner=user)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)

    client.login(user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": project.pk, "email": "test@test.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_api_create_membership_without_enough_memberships_public_project_slots_one_projects(client):
    user = f.UserFactory.create(max_memberships_public_projects=1)
    project = f.ProjectFactory(owner=user, is_private=False)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    client.login(user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": project.pk, "email": "test@test.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "reached your current limit of memberships for public" in response.data["_error_message"]


def test_api_create_membership_with_enough_memberships_public_project_slots_multiple_projects(client):
    user = f.UserFactory.create(max_memberships_public_projects=5)
    project = f.ProjectFactory(owner=user, is_private=False)
    role = f.RoleFactory(project=project, name="Test")
    f.MembershipFactory(project=project, user=user, is_admin=True)

    other_project = f.ProjectFactory(owner=user)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)
    f.MembershipFactory.create(project=other_project)

    client.login(user)
    url = reverse("memberships-list")
    data = {"role": role.pk, "project": project.pk, "email": "test@test.com"}
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_api_edit_membership(client):
    membership = f.MembershipFactory(is_admin=True)
    client.login(membership.user)
    url = reverse("memberships-detail", args=[membership.id])
    data = {"email": "new@email.com"}
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200

def test_api_change_owner_membership_to_no_admin_return_error(client):
    project = f.ProjectFactory()
    membership_owner = f.MembershipFactory(project=project, user=project.owner, is_admin=True)
    membership = f.MembershipFactory(project=project, is_admin=True)

    url = reverse("memberships-detail", args=[membership_owner.id])
    data = {"is_admin": False}

    client.login(membership.user)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 400
    assert 'is_admin' in response.data


def test_api_delete_membership(client):
    membership = f.MembershipFactory(is_admin=True)
    client.login(membership.user)
    url = reverse("memberships-detail", args=[membership.id])
    response = client.json.delete(url)

    assert response.status_code == 400

    f.MembershipFactory(is_admin=True, project=membership.project)

    url = reverse("memberships-detail", args=[membership.id])
    response = client.json.delete(url)

    assert response.status_code == 204


def test_api_delete_membership_without_user(client):
    membership_owner = f.MembershipFactory(is_admin=True)
    membership_without_user_one = f.MembershipFactory(project=membership_owner.project, user=None)
    f.MembershipFactory(project=membership_owner.project, user=None)
    client.login(membership_owner.user)
    url = reverse("memberships-detail", args=[membership_without_user_one.id])
    response = client.json.delete(url)

    assert response.status_code == 204
