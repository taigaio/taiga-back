from django.core.urlresolvers import reverse
from taiga.base.utils import json
from taiga.projects.services import stats as stats_services
from taiga.projects.history.services import take_snapshot

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_create_project(client):
    user = f.create_user()
    url = reverse("projects-list")
    data = {"name": "project name", "description": "project description"}

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_partially_update_project(client):
    project = f.create_project()
    f.MembershipFactory(user=project.owner, project=project, is_owner=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})
    data = {"name": ""}

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_us_status_slug_generation(client):
    us_status = f.UserStoryStatusFactory(name="NEW")
    f.MembershipFactory(user=us_status.project.owner, project=us_status.project, is_owner=True)
    assert us_status.slug == "new"

    client.login(us_status.project.owner)

    url = reverse("userstory-statuses-detail", kwargs={"pk": us_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_task_status_slug_generation(client):
    task_status = f.TaskStatusFactory(name="NEW")
    f.MembershipFactory(user=task_status.project.owner, project=task_status.project, is_owner=True)
    assert task_status.slug == "new"

    client.login(task_status.project.owner)

    url = reverse("task-statuses-detail", kwargs={"pk": task_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_issue_status_slug_generation(client):
    issue_status = f.IssueStatusFactory(name="NEW")
    f.MembershipFactory(user=issue_status.project.owner, project=issue_status.project, is_owner=True)
    assert issue_status.slug == "new"

    client.login(issue_status.project.owner)

    url = reverse("issue-statuses-detail", kwargs={"pk": issue_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_points_name_duplicated(client):
    point_1 = f.PointsFactory()
    point_2 = f.PointsFactory(project=point_1.project)
    f.MembershipFactory(user=point_1.project.owner, project=point_1.project, is_owner=True)
    client.login(point_1.project.owner)

    url = reverse("points-detail", kwargs={"pk": point_2.pk})
    data = {"name": point_1.name}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400
    assert response.data["name"][0] == "Name duplicated for the project"


def test_update_points_when_not_null_values_for_points(client):
    points = f.PointsFactory(name="?", value="6")
    role = f.RoleFactory(project=points.project, computable=True)
    assert points.project.points.filter(value__isnull=True).count() == 0
    points.project.update_role_points()
    assert points.project.points.filter(value__isnull=True).count() == 1


def test_get_closed_bugs_per_member_stats():
    project = f.ProjectFactory()
    membership_1 = f.MembershipFactory(project=project)
    membership_2 = f.MembershipFactory(project=project)
    issue_closed_status = f.IssueStatusFactory(is_closed=True, project=project)
    issue_open_status = f.IssueStatusFactory(is_closed=False, project=project)
    issue_closed = f.IssueFactory(project=project,
                                  status=issue_closed_status,
                                  owner=membership_1.user,
                                  assigned_to=membership_1.user)
    issue_open = f.IssueFactory(project=project,
                                status=issue_open_status,
                                owner=membership_2.user,
                                assigned_to=membership_2.user)
    task_closed_status = f.TaskStatusFactory(is_closed=True, project=project)
    task_open_status = f.TaskStatusFactory(is_closed=False, project=project)
    task_closed = f.TaskFactory(project=project,
                              status=task_closed_status,
                              owner=membership_1.user,
                              assigned_to=membership_1.user)
    task_open = f.TaskFactory(project=project,
                                status=task_open_status,
                                owner=membership_2.user,
                                assigned_to=membership_2.user)
    task_iocaine = f.TaskFactory(project=project,
                                status=task_open_status,
                                owner=membership_2.user,
                                assigned_to=membership_2.user,
                                is_iocaine=True)

    wiki_page = f.WikiPageFactory.create(project=project, owner=membership_1.user)
    take_snapshot(wiki_page, user=membership_1.user)
    wiki_page.content="Frontend, future"
    wiki_page.save()
    take_snapshot(wiki_page, user=membership_1.user)

    stats = stats_services.get_member_stats_for_project(project)

    assert stats["closed_bugs"][membership_1.user.id] == 1
    assert stats["closed_bugs"][membership_2.user.id] == 0

    assert stats["iocaine_tasks"][membership_1.user.id] == 0
    assert stats["iocaine_tasks"][membership_2.user.id] == 1

    assert stats["wiki_changes"][membership_1.user.id] == 2
    assert stats["wiki_changes"][membership_2.user.id] == 0

    assert stats["created_bugs"][membership_1.user.id] == 1
    assert stats["created_bugs"][membership_2.user.id] == 1

    assert stats["closed_tasks"][membership_1.user.id] == 1
    assert stats["closed_tasks"][membership_2.user.id] == 0


def test_leave_project_valid_membership(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 200


def test_leave_project_valid_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 403
    assert json.loads(response.content)["_error_message"] == "You can't leave the project if there are no more owners"


def test_leave_project_invalid_membership(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory()
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 404


def test_delete_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    client.login(user)
    url = reverse("memberships-detail", args=(membership.id,))
    response = client.delete(url)
    assert response.status_code == 400
    assert json.loads(response.content)["_error_message"] == "At least one of the user must be an active admin"


def test_edit_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    data = {
        "is_owner": False
    }
    client.login(user)
    url = reverse("memberships-detail", args=(membership.id,))
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400
    assert response.data["is_owner"][0] == "At least one of the user must be an active admin"
