import pytest

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_create_user_story_attachment_without_file(client):
    """
    Bug test "Don't create attachments without attached_file"
    """
    us = f.UserStoryFactory.create()
    f.MembershipFactory(project=us.project, user=us.owner, is_owner=True)
    attachment_data = {
        "description": "test",
        "attached_file": None,
        "project": us.project_id,
    }

    url = reverse('userstory-attachments-list')

    client.login(us.owner)
    response = client.post(url, attachment_data)
    assert response.status_code == 400


def test_create_attachment_on_wrong_project(client):
    issue1 = f.create_issue()
    issue2 = f.create_issue(owner=issue1.owner)
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_owner=True)

    assert issue1.owner == issue2.owner
    assert issue1.project.owner == issue2.project.owner

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue2.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile("test.txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.status_code == 400


def test_create_attachment_with_long_file_name(client):
    issue1 = f.create_issue()
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_owner=True)

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue1.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile(500*"x"+".txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.data["attached_file"].endswith("/"+100*"x"+".txt")
