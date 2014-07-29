import pytest

from django.core.urlresolvers import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_api_filter_by_subject(client):
    f.create_issue()
    issue = f.create_issue(subject="some random subject")
    url = reverse("issues-list") + "?subject=some subject"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1, number_of_issues
