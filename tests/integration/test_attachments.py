import pytest

from django.core.urlresolvers import reverse
from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile

from .. import factories as f
from ..utils import set_settings

from taiga.projects.attachments.serializers import AttachmentSerializer

pytestmark = pytest.mark.django_db


def test_authentication(client):
    "User can't access an attachment if not authenticated"
    attachment = f.UserStoryAttachmentFactory.create()
    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    response = client.get(url)

    assert response.status_code == 401


def test_authorization(client):
    "User can't access an attachment if not authorized"
    attachment = f.UserStoryAttachmentFactory.create()
    user = f.UserFactory.create()

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(user)
    response = client.get(url)

    assert response.status_code == 403


@set_settings(IN_DEVELOPMENT_SERVER=True)
def test_attachment_redirect_in_devserver(client):
    "When accessing the attachment in devserver redirect to the real attachment url"
    attachment = f.UserStoryAttachmentFactory.create(attached_file="test")

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(attachment.owner)
    response = client.get(url)

    assert response.status_code == 302


@set_settings(IN_DEVELOPMENT_SERVER=False)
def test_attachment_redirect(client):
    "When accessing the attachment redirect using X-Accel-Redirect header"
    attachment = f.UserStoryAttachmentFactory.create()

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(attachment.owner)
    response = client.get(url)

    assert response.status_code == 200
    assert response.has_header('x-accel-redirect')


# Bug test "Don't create attachments without attached_file"
def test_create_user_story_attachment_without_file(client):
    us = f.UserStoryFactory.create()
    attachment = f.UserStoryAttachmentFactory(project=us.project, content_object=us)

    attachment_data = AttachmentSerializer(attachment).data
    attachment_data["id"] = None
    attachment_data["description"] = "test"
    attachment_data["attached_file"] = None

    url = reverse('userstory-attachments-list')

    client.login(us.owner)
    response = client.post(url, attachment_data)
    assert response.status_code == 400


def test_create_attachment_on_wrong_project(client):
    issue1 = f.create_issue()
    issue2 = f.create_issue(owner=issue1.owner)

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
