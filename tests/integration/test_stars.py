import pytest
from django.core.urlresolvers import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_project_owner_star_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    url = reverse("projects-star", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_owner_unstar_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    url = reverse("projects-unstar", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_member_star_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role)
    url = reverse("projects-star", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_project_member_unstar_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role)
    url = reverse("projects-unstar", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200
