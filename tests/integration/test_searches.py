import pytest

from django.core.urlresolvers import reverse

from .. import factories as f


pytestmark = pytest.mark.django_db

@pytest.fixture
def searches_initial_data():
    m = type("InitialData", (object,), {})()

    m.project1 = f.ProjectFactory.create()
    m.project2 = f.ProjectFactory.create()

    m.member1 = f.MembershipFactory.create(project=m.project1)
    m.member2 = f.MembershipFactory.create(project=m.project1)

    m.us1 = f.UserStoryFactory.create(project=m.project1)
    m.us2 = f.UserStoryFactory.create(project=m.project1, description="Back to the future")
    m.us3 = f.UserStoryFactory.create(project=m.project2)

    m.tsk1 = f.TaskFactory.create(project=m.project2)
    m.tsk2 = f.TaskFactory.create(project=m.project1)
    m.tsk3 = f.TaskFactory.create(project=m.project1, subject="Back to the future")

    m.iss1 = f.IssueFactory.create(project=m.project1, subject="Backend and Frontend")
    m.iss2 = f.IssueFactory.create(project=m.project2)
    m.iss3 = f.IssueFactory.create(project=m.project1)

    m.wiki1  = f.WikiPageFactory.create(project=m.project1)
    m.wiki2  = f.WikiPageFactory.create(project=m.project1, content="Frontend, future")
    m.wiki3  = f.WikiPageFactory.create(project=m.project2)

    return m


def test_search_all_objects_in_my_project(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project1.id})
    assert response.status_code == 200
    assert response.data["count"] == 8
    assert len(response.data["userstories"]) == 2
    assert len(response.data["tasks"]) == 2
    assert len(response.data["issues"]) == 2
    assert len(response.data["wikipages"]) == 2


def test_search_all_objects_in_project_is_not_mine(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project2.id})
    assert response.status_code == 403


def test_search_text_query_in_my_project(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project1.id, "text": "future"})
    assert response.status_code == 200
    assert response.data["count"] == 3
    assert len(response.data["userstories"]) == 1
    assert len(response.data["tasks"]) == 1
    assert len(response.data["issues"]) == 0
    assert len(response.data["wikipages"]) == 1

    response = client.get(reverse("search-list"), {"project": data.project1.id, "text": "back"})
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["userstories"]) == 1
    assert len(response.data["tasks"]) == 1
    assert len(response.data["issues"]) == 0
    assert len(response.data["wikipages"]) == 0
