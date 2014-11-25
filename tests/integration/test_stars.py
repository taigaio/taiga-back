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

import pytest
from django.core.urlresolvers import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_project_owner_star_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, is_owner=True, user=user)
    url = reverse("projects-star", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_owner_unstar_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, is_owner=True, user=user)
    url = reverse("projects-unstar", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_member_star_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    url = reverse("projects-star", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_member_unstar_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    url = reverse("projects-unstar", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_project_fans(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    fan = f.VoteFactory.create(content_object=project)
    url = reverse("projects-fans", args=(project.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == fan.user.id


def test_list_user_starred_projects(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory()
    url = reverse("users-starred", args=(user.id,))
    f.VoteFactory.create(user=user, content_object=project)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == project.id


def test_get_project_stars(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-detail", args=(project.id,))
    f.VotesFactory.create(content_object=project, count=5)
    f.VotesFactory.create(count=3)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['stars'] == 5
