import pytest
import json

from django.core.urlresolvers import reverse
from .. import factories as f


pytestmark = pytest.mark.django_db


def test_archived_filter(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    userstory_1 = f.UserStoryFactory.create(project=project)
    user_story_2 = f.UserStoryFactory.create(is_archived=True, project=project)

    client.login(user)

    url = reverse("userstories-list")

    data = {}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 2

    data = {"is_archived": 0}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 1

    data = {"is_archived": 1}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 1
