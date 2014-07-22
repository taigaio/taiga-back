import pytest

from django.core.urlresolvers import reverse
from django.core.files.base import File

from .. import factories as f
from ..utils import set_settings

pytestmark = pytest.mark.django_db

def test_authentication(client):
    "User can't access an attachment if not authenticated"
    attachment = f.AttachmentFactory.create()
    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    response = client.get(url)

    assert response.status_code == 401


def test_authorization(client):
    "User can't access an attachment if not authorized"
    attachment = f.AttachmentFactory.create()
    user = f.UserFactory.create()

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(user)
    response = client.get(url)

    assert response.status_code == 403


@set_settings(IN_DEVELOPMENT_SERVER=True)
def test_attachment_redirect_in_devserver(client):
    "When accessing the attachment in devserver redirect to the real attachment url"
    attachment = f.AttachmentFactory.create()

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(attachment.owner)
    response = client.get(url)

    assert response.status_code == 302


@set_settings(IN_DEVELOPMENT_SERVER=False)
def test_attachment_redirect(client):
    "When accessing the attachment redirect using X-Accel-Redirect header"
    attachment = f.AttachmentFactory.create()

    url = reverse("attachment-url", kwargs={"pk": attachment.pk})

    client.login(attachment.owner)
    response = client.get(url)

    assert response.status_code == 200
    assert response.has_header('x-accel-redirect')
