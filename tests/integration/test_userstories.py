import copy
from unittest import mock
from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.userstories import services, models

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_userstories_from_bulk():
    data = "User Story #1\nUser Story #2\n"
    userstories = services.get_userstories_from_bulk(data)

    assert len(userstories) == 2
    assert userstories[0].subject == "User Story #1"
    assert userstories[1].subject == "User Story #2"


def test_create_userstories_in_bulk():
    data = "User Story #1\nUser Story #2\n"

    with mock.patch("taiga.projects.userstories.services.db") as db:
        userstories = services.create_userstories_in_bulk(data)
        db.save_in_bulk.assert_called_once_with(userstories, None, None)


def test_update_userstories_order_in_bulk():
    data = [{"us_id": 1, "order": 1}, {"us_id": 2, "order": 2}]

    project = mock.Mock()
    project.pk = 1

    with mock.patch("taiga.projects.userstories.services.db") as db:
        services.update_userstories_order_in_bulk(data, "backlog_order", project)
        db.update_in_bulk_with_ids.assert_called_once_with([1, 2],
                                                           [{"backlog_order": 1},
                                                            {"backlog_order": 2}],
                                                           model=models.UserStory)


def test_api_delete_userstory(client):
    us = f.create_userstory()
    url = reverse("userstories-detail", kwargs={"pk": us.pk})

    client.login(us.owner)
    response = client.delete(url)

    assert response.status_code == 204


def test_api_filter_by_subject(client):
    f.create_userstory()
    us = f.create_userstory(subject="some random subject")
    url = reverse("userstories-list") + "?subject=some subject"

    client.login(us.owner)
    response = client.get(url)
    number_of_stories = len(response.data)

    assert response.status_code == 200
    assert number_of_stories == 1, number_of_stories


def test_api_create_in_bulk_with_status(client):
    project = f.create_project()
    url = reverse("userstories-bulk-create")
    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "status_id": project.default_us_status.id
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data
    assert response.data[0]["status"] == project.default_us_status.id


def test_api_update_backlog_order_in_bulk(client):
    project = f.create_project()
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)

    url1 = reverse("userstories-bulk-update-backlog-order")
    url2 = reverse("userstories-bulk-update-kanban-order")
    url3 = reverse("userstories-bulk-update-sprint-order")

    data = {
        "project_id": project.id,
        "bulk_stories": [{"us_id": us1.id, "order": 1},
                         {"us_id": us2.id, "order": 2}]
    }

    client.login(project.owner)

    response1 = client.json.post(url1, json.dumps(data))
    response2 = client.json.post(url2, json.dumps(data))
    response3 = client.json.post(url3, json.dumps(data))

    assert response1.status_code == 204, response.data
    assert response2.status_code == 204, response.data
    assert response3.status_code == 204, response.data


from taiga.projects.userstories.serializers import UserStorySerializer


def test_update_userstory_points(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    member = f.MembershipFactory.create(project=project, user=user1, role=role1)
    member = f.MembershipFactory.create(project=project, user=user2, role=role2)

    points1 = f.PointsFactory.create(project=project, value=None)
    points2 = f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    us = f.UserStoryFactory.create(project=project, owner=user1)
    url = reverse("userstories-detail", args=[us.pk])
    usdata = UserStorySerializer(us).data

    client.login(user1)

    # Api should ignore invalid values
    data = {}
    data["version"] = usdata["version"]
    data["points"] = copy.copy(usdata["points"])
    data["points"].update({'2000':points3.pk})

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    # Api should save successful
    data = {}
    data["version"] = usdata["version"]
    data["points"] = copy.copy(usdata["points"])
    data["points"].update({str(role1.pk):points3.pk})

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    us = models.UserStory.objects.get(pk=us.pk)
    rp = list(us.role_points.values_list("role_id", "points_id"))

    assert rp == [(role1.pk, points3.pk), (role2.pk, points1.pk)]


def test_update_userstory_rolepoints_on_add_new_role(client):
    # This test is explicitly without assertions. It simple should
    # works without raising any exception.

    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)

    member1 = f.MembershipFactory.create(project=project, user=user1, role=role1)

    points1 = f.PointsFactory.create(project=project, value=2)

    us = f.UserStoryFactory.create(project=project, owner=user1)
    # url = reverse("userstories-detail", args=[us.pk])
    # client.login(user1)

    role2 = f.RoleFactory.create(project=project, computable=True)
    member2 = f.MembershipFactory.create(project=project, user=user2, role=role2)
    us.save()


def test_archived_filter(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user)
    f.UserStoryFactory.create(project=project)
    f.UserStoryFactory.create(is_archived=True, project=project)

    client.login(user)

    url = reverse("userstories-list")

    data = {}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 2

    data = {"is_archived": 0}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 1

    data = {"is_archived": 1}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 1
