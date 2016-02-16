from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files import File

from taiga.base.utils import json
from taiga.projects.services import stats as stats_services
from taiga.projects.history.services import take_snapshot
from taiga.permissions.permissions import ANON_PERMISSIONS
from taiga.projects.models import Project

from .. import factories as f
from ..utils import DUMMY_BMP_DATA

from tempfile import NamedTemporaryFile
from easy_thumbnails.files import generate_all_aliases, get_thumbnailer

import os.path
import pytest

pytestmark = pytest.mark.django_db


def test_get_project_by_slug(client):
    project = f.create_project()
    url = reverse("projects-detail", kwargs={"pk": project.slug})

    response = client.json.get(url)
    assert response.status_code == 404

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 404


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


def test_us_status_is_closed_changed_recalc_us_is_closed(client):
    us_status = f.UserStoryStatusFactory(is_closed=False)
    user_story = f.UserStoryFactory.create(project=us_status.project, status=us_status)

    assert user_story.is_closed is False

    us_status.is_closed = True
    us_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is True

    us_status.is_closed = False
    us_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is False


def test_task_status_is_closed_changed_recalc_us_is_closed(client):
    us_status = f.UserStoryStatusFactory()
    user_story = f.UserStoryFactory.create(project=us_status.project, status=us_status)
    task_status = f.TaskStatusFactory.create(project=us_status.project, is_closed=False)
    task = f.TaskFactory.create(project=us_status.project, status=task_status, user_story=user_story)

    assert user_story.is_closed is False

    task_status.is_closed = True
    task_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is True

    task_status.is_closed = False
    task_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is False


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
    f.RoleFactory(project=points.project, computable=True)
    assert points.project.points.filter(value__isnull=True).count() == 0
    points.project.update_role_points()
    assert points.project.points.filter(value__isnull=True).count() == 1


def test_get_closed_bugs_per_member_stats():
    project = f.ProjectFactory()
    membership_1 = f.MembershipFactory(project=project)
    membership_2 = f.MembershipFactory(project=project)
    issue_closed_status = f.IssueStatusFactory(is_closed=True, project=project)
    issue_open_status = f.IssueStatusFactory(is_closed=False, project=project)
    f.IssueFactory(project=project,
                   status=issue_closed_status,
                   owner=membership_1.user,
                   assigned_to=membership_1.user)
    f.IssueFactory(project=project,
                   status=issue_open_status,
                   owner=membership_2.user,
                   assigned_to=membership_2.user)
    task_closed_status = f.TaskStatusFactory(is_closed=True, project=project)
    task_open_status = f.TaskStatusFactory(is_closed=False, project=project)
    f.TaskFactory(project=project,
                  status=task_closed_status,
                  owner=membership_1.user,
                  assigned_to=membership_1.user)
    f.TaskFactory(project=project,
                  status=task_open_status,
                  owner=membership_2.user,
                  assigned_to=membership_2.user)
    f.TaskFactory(project=project,
                  status=task_open_status,
                  owner=membership_2.user,
                  assigned_to=membership_2.user,
                  is_iocaine=True)

    wiki_page = f.WikiPageFactory.create(project=project, owner=membership_1.user)
    take_snapshot(wiki_page, user=membership_1.user)
    wiki_page.content = "Frontend, future"
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
    assert response.data["_error_message"] == "You can't leave the project if there are no more owners"


def test_leave_project_invalid_membership(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory()
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 404


def test_leave_project_respect_watching_items(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    issue = f.IssueFactory(owner=user)
    issue.watchers=[user]
    issue.save()

    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 200
    assert issue.watchers == [user]


def test_delete_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    client.login(user)
    url = reverse("memberships-detail", args=(membership.id,))
    response = client.delete(url)
    assert response.status_code == 400
    assert response.data["_error_message"] == "At least one of the user must be an active admin"


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


def test_anon_permissions_generation_when_making_project_public(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=True)
    role = f.RoleFactory.create(project=project, permissions=["view_project", "modify_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    assert project.anon_permissions == []
    client.login(user)
    url = reverse("projects-detail", kwargs={"pk": project.pk})
    data = {"is_private": False}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    assert set(anon_permissions).issubset(set(response.data["anon_permissions"]))
    assert set(anon_permissions).issubset(set(response.data["public_permissions"]))


def test_destroy_point_and_reassign(client):
    project = f.ProjectFactory.create()
    f.MembershipFactory.create(project=project, user=project.owner, is_owner=True)
    p1 = f.PointsFactory(project=project)
    project.default_points = p1
    project.save()
    p2 = f.PointsFactory(project=project)
    user_story =  f.UserStoryFactory.create(project=project)
    rp1 = f.RolePointsFactory.create(user_story=user_story, points=p1)

    url = reverse("points-detail", args=[p1.pk]) + "?moveTo={}".format(p2.pk)

    client.login(project.owner)

    assert user_story.role_points.all()[0].points.id == p1.id
    assert project.default_points.id == p1.id

    response = client.delete(url)

    assert user_story.role_points.all()[0].points.id == p2.id
    project = Project.objects.get(id=project.id)
    assert project.default_points.id == p2.id


def test_update_projects_order_in_bulk(client):
    user = f.create_user()
    client.login(user)
    membership_1 = f.MembershipFactory(user=user)
    membership_2 = f.MembershipFactory(user=user)

    url = reverse("projects-bulk-update-order")
    data = [
        {"project_id": membership_1.project.id, "order":100},
        {"project_id": membership_2.project.id, "order":200}
    ]

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204
    assert user.memberships.get(project=membership_1.project).user_order == 100
    assert user.memberships.get(project=membership_2.project).user_order == 200


def test_create_and_use_template(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    role = f.RoleFactory(project=project)
    f.MembershipFactory(user=user, project=project, is_owner=True, role=role)
    client.login(user)

    url = reverse("projects-create-template", kwargs={"pk": project.pk})
    data = {
        "template_name": "test template",
        "template_description": "test template description"
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201

    template_id = response.data["id"]
    url = reverse("projects-list")
    data = {
        "name": "test project based on template",
        "description": "test project based on template",
        "creation_template": template_id,
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201


def test_projects_user_order(client):
    user = f.UserFactory.create(is_superuser=True)
    project_1 = f.create_project()
    role_1 = f.RoleFactory(project=project_1)
    f.MembershipFactory(user=user, project=project_1, is_owner=True, role=role_1, user_order=2)

    project_2 = f.create_project()
    role_2 = f.RoleFactory(project=project_2)
    f.MembershipFactory(user=user, project=project_2, is_owner=True, role=role_2, user_order=1)

    client.login(user)
    #Testing default id order
    url = reverse("projects-list")
    url = "%s?member=%s" % (url, user.id)
    response = client.json.get(url)
    response_content = response.data
    assert response.status_code == 200
    assert(response_content[0]["id"] == project_1.id)

    #Testing user order
    url = reverse("projects-list")
    url = "%s?member=%s&order_by=memberships__user_order" % (url, user.id)
    response = client.json.get(url)
    response_content = response.data
    assert response.status_code == 200
    assert(response_content[0]["id"] == project_2.id)


@pytest.mark.django_db(transaction=True)
def test_update_project_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-change-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)

        client.login(user)
        post_data = {'logo': logo}
        response = client.post(url, post_data)
        assert response.status_code == 200
        assert not any(list(map(os.path.exists, original_photo_paths)))


@pytest.mark.django_db(transaction=True)
def test_update_project_logo_with_long_file_name(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-change-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.name=500*"x"+".bmp"
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)

        client.login(user)
        post_data = {'logo': logo}
        response = client.post(url, post_data)

        assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_remove_project_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-remove-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))
    client.login(user)
    response = client.post(url)
    assert response.status_code == 200
    assert not any(list(map(os.path.exists, original_photo_paths)))

@pytest.mark.django_db(transaction=True)
def test_remove_project_with_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-detail", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))
    client.login(user)
    response = client.delete(url)
    assert response.status_code == 204
    assert not any(list(map(os.path.exists, original_photo_paths)))


def test_project_list_without_search_query_order_by_name(client):
    user = f.UserFactory.create(is_superuser=True)
    project3 = f.create_project(name="test 3 - word", description="description 3", tags=["tag3"])
    project1 = f.create_project(name="test 1", description="description 1 - word", tags=["tag1"])
    project2 = f.create_project(name="test 2", description="description 2", tags=["word", "tag2"])

    url = reverse("projects-list")

    client.login(user)
    response = client.json.get(url)

    assert response.status_code == 200
    assert response.data[0]["id"] == project1.id
    assert response.data[1]["id"] == project2.id
    assert response.data[2]["id"] == project3.id


def test_project_list_with_search_query_order_by_ranking(client):
    user = f.UserFactory.create(is_superuser=True)
    project3 = f.create_project(name="test 3 - word", description="description 3", tags=["tag3"])
    project1 = f.create_project(name="test 1", description="description 1 - word", tags=["tag1"])
    project2 = f.create_project(name="test 2", description="description 2", tags=["word", "tag2"])
    project4 = f.create_project(name="test 4", description="description 4", tags=["tag4"])
    project5 = f.create_project(name="test 5", description="description 5", tags=["tag5"])

    url = reverse("projects-list")

    client.login(user)
    response = client.json.get(url, {"q": "word"})

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]["id"] == project3.id
    assert response.data[1]["id"] == project2.id
    assert response.data[2]["id"] == project1.id
