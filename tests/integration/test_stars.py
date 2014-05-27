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


def test_list_project_fans(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    fan = f.FanFactory.create(project=project)
    url = reverse("project-fans-list", args=(project.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == fan.user.id


def test_get_project_fan(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    fan = f.FanFactory.create(project=project)
    url = reverse("project-fans-detail", args=(project.id, fan.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == fan.user.id


def test_list_user_starred_projects(client):
    user = f.UserFactory.create()
    fan = f.FanFactory.create(user=user)
    url = reverse("user-starred-list", args=(user.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == fan.project.id


def test_get_user_starred_project(client):
    user = f.UserFactory.create()
    fan = f.FanFactory.create(user=user)
    url = reverse("user-starred-detail", args=(user.id, fan.project.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == fan.project.id


def test_get_project_stars(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.StarsFactory.create(project=project, count=5)
    url = reverse("projects-detail", args=(project.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['stars'] == 5
