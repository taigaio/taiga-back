# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from django.core import mail
from django.urls import reverse

from tests import factories as f

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


# Members can comment on a private project
# if the project has the contact activated
def test_member_create_comment_on_private_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=True)
    project.is_contact_activated = True
    m1 = f.MembershipFactory(user=project.owner, project=project)
    m2 = f.MembershipFactory(project=project, is_admin=True)
    m3 = f.MembershipFactory(user=user, project=project, is_admin=False)

    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    assert len(mail.outbox) == 0
    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 201
    assert len(mail.outbox) == 2
    assert set([to for out in mail.outbox for to in out.to]) == set([project.owner.email, m2.user.email])


# Non members user cannot comment on a private project
# even if the project has the contact activated
def test_guest_create_comment_on_private_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=True)
    project.is_contact_activated = True

    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 403
    assert len(mail.outbox) == 0


# All user can comment on a public project
# if the project has the contact activated
def test_create_comment_on_public_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=False)
    project.is_contact_activated = True
    m1 = f.MembershipFactory(user=project.owner, project=project)
    m2 = f.MembershipFactory(project=project, is_admin=True)
    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    assert len(mail.outbox) == 0
    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 201
    assert len(mail.outbox) == 2
    assert set([to for out in mail.outbox for to in out.to]) == set([project.owner.email, m2.user.email])


# No user can comment on a project
# if the project does not have the contact activated
def test_create_comment_disabled(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    project.is_contact_activated = False
    project.save()
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)

    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 403
