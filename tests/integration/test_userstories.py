import copy
import uuid
import csv

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


def test_create_userstory_without_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    status = f.UserStoryStatusFactory.create(project=project)
    project.default_us_status = status
    project.save()

    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] == project.default_us_status.id


def test_api_delete_userstory(client):
    us = f.UserStoryFactory.create()
    f.MembershipFactory.create(project=us.project, user=us.owner, is_owner=True)
    url = reverse("userstories-detail", kwargs={"pk": us.pk})

    client.login(us.owner)
    response = client.delete(url)

    assert response.status_code == 204


def test_api_filter_by_subject_or_ref(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)

    f.UserStoryFactory.create(project=project)
    f.UserStoryFactory.create(project=project, subject="some random subject")
    url = reverse("userstories-list") + "?q=some subject"

    client.login(project.owner)
    response = client.get(url)
    number_of_stories = len(response.data)

    assert response.status_code == 200
    assert number_of_stories == 1, number_of_stories


def test_api_create_in_bulk_with_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_owner=True)
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
    f.MembershipFactory.create(project=project, user=project.owner, is_owner=True)
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

    assert response1.status_code == 204, response1.data
    assert response2.status_code == 204, response2.data
    assert response3.status_code == 204, response3.data


from taiga.projects.userstories.serializers import UserStorySerializer


def test_update_userstory_points(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    f.MembershipFactory.create(project=project, user=user1, role=role1, is_owner=True)
    f.MembershipFactory.create(project=project, user=user2, role=role2)

    f.PointsFactory.create(project=project, value=None)
    f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    us = f.UserStoryFactory.create(project=project, owner=user1)
    usdata = UserStorySerializer(us).data

    url = reverse("userstories-detail", args=[us.pk])

    client.login(user1)

    # Api should ignore invalid values
    data = {}
    data["version"] = usdata["version"]
    data["points"] = copy.copy(usdata["points"])
    data["points"].update({'2000': points3.pk})

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["points"] == usdata['points']

    # Api should save successful
    data = {}
    data["version"] = usdata["version"] + 1
    data["points"] = copy.copy(usdata["points"])
    data["points"].update({str(role1.pk): points3.pk})

    response = client.json.patch(url, json.dumps(data))
    us = models.UserStory.objects.get(pk=us.pk)
    usdatanew = UserStorySerializer(us).data
    assert response.status_code == 200
    assert response.data["points"] == usdatanew['points']
    assert response.data["points"] != usdata['points']


def test_update_userstory_rolepoints_on_add_new_role(client):
    # This test is explicitly without assertions. It simple should
    # works without raising any exception.

    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)

    f.MembershipFactory.create(project=project, user=user1, role=role1)

    f.PointsFactory.create(project=project, value=2)

    us = f.UserStoryFactory.create(project=project, owner=user1)
    # url = reverse("userstories-detail", args=[us.pk])
    # client.login(user1)

    role2 = f.RoleFactory.create(project=project, computable=True)
    f.MembershipFactory.create(project=project, user=user2, role=role2)
    us.save()


def test_archived_filter(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    f.UserStoryFactory.create(project=project)
    archived_status = f.UserStoryStatusFactory.create(is_archived=True)
    f.UserStoryFactory.create(status=archived_status, project=project)

    client.login(user)

    url = reverse("userstories-list")

    data = {}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 2

    data = {"status__is_archived": 0}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 1

    data = {"status__is_archived": 1}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 1


def test_filter_by_multiple_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    f.UserStoryFactory.create(project=project)
    us1 = f.UserStoryFactory.create(project=project)
    us2 = f.UserStoryFactory.create(project=project)

    client.login(user)

    url = reverse("userstories-list")
    url = "{}?status={},{}".format(reverse("userstories-list"), us1.status.id, us2.status.id)


    data = {}
    response = client.get(url, data)
    assert len(json.loads(response.content)) == 2


def test_get_total_points(client):
    project = f.ProjectFactory.create()

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    points1 = f.PointsFactory.create(project=project, value=None)
    points2 = f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    us_with_points = f.UserStoryFactory.create(project=project)
    us_with_points.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_with_points, role=role1, points=points2)
    f.RolePointsFactory.create(user_story=us_with_points, role=role2, points=points3)

    assert us_with_points.get_total_points() == 3.0

    us_without_points = f.UserStoryFactory.create(project=project)
    us_without_points.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_without_points, role=role1, points=points1)
    f.RolePointsFactory.create(user_story=us_without_points, role=role2, points=points1)

    assert us_without_points.get_total_points() is None

    us_mixed = f.UserStoryFactory.create(project=project)
    us_mixed.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_mixed, role=role1, points=points1)
    f.RolePointsFactory.create(user_story=us_mixed, role=role2, points=points2)

    assert us_mixed.get_total_points() == 1.0


def test_get_invalid_csv(client):
    url = reverse("userstories-csv")

    response = client.get(url)
    assert response.status_code == 404

    response = client.get("{}?uuid={}".format(url, "not-valid-uuid"))
    assert response.status_code == 404


def test_get_valid_csv(client):
    url = reverse("userstories-csv")
    project = f.ProjectFactory.create(userstories_csv_uuid=uuid.uuid4().hex)

    response = client.get("{}?uuid={}".format(url, project.userstories_csv_uuid))
    assert response.status_code == 200


def test_custom_fields_csv_generation():
    project = f.ProjectFactory.create(userstories_csv_uuid=uuid.uuid4().hex)
    attr = f.UserStoryCustomAttributeFactory.create(project=project, name="attr1", description="desc")
    us = f.UserStoryFactory.create(project=project)
    attr_values = us.custom_attributes_values
    attr_values.attributes_values = {str(attr.id):"val1"}
    attr_values.save()
    queryset = project.user_stories.all()
    data = services.userstories_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)
    assert row[24] == attr.name
    row = next(reader)
    assert row[24] == "val1"
