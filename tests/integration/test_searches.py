# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from django.core.urlresolvers import reverse

from .. import factories as f

from taiga.permissions.choices import MEMBERS_PERMISSIONS
from tests.utils import disconnect_signals, reconnect_signals


pytestmark = pytest.mark.django_db(transaction=True)


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def searches_initial_data():
    m = type("InitialData", (object,), {})()

    m.project1 = f.ProjectFactory.create()
    m.project2 = f.ProjectFactory.create()

    m.member1 = f.MembershipFactory(project=m.project1,
                                    role__project=m.project1,
                                    role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.member2 = f.MembershipFactory(project=m.project1,
                                    role__project=m.project1,
                                    role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))


    m.epic11 = f.EpicFactory(project=m.project1, subject="Back to the future")
    m.epic12 = f.EpicFactory(project=m.project1, tags=["Back", "future"])
    m.epic13 = f.EpicFactory(project=m.project1)
    m.epic14 = f.EpicFactory(project=m.project1, description="Backend to the future")
    m.epic21 = f.EpicFactory(project=m.project2, subject="Back to the future")

    m.us11 = f.UserStoryFactory(project=m.project1, subject="Back to the future")
    m.us12 = f.UserStoryFactory(project=m.project1, description="Back to the future")
    m.us13 = f.UserStoryFactory(project=m.project1, tags=["Backend", "future"])
    m.us14 = f.UserStoryFactory(project=m.project1)
    m.us21 = f.UserStoryFactory(project=m.project2, subject="Backend to the future")

    m.task11 = f.TaskFactory(project=m.project1, subject="Back to the future")
    m.task12 = f.TaskFactory(project=m.project1, tags=["Back", "future"])
    m.task13 = f.TaskFactory(project=m.project1)
    m.task14 = f.TaskFactory(project=m.project1, description="Backend to the future")
    m.task21 = f.TaskFactory(project=m.project2, subject="Back to the future")

    m.issue11 = f.IssueFactory(project=m.project1, description="Back to the future")
    m.issue12 = f.IssueFactory(project=m.project1, tags=["back", "future"])
    m.issue13 = f.IssueFactory(project=m.project1)
    m.issue14 = f.IssueFactory(project=m.project1, subject="Backend to the future")
    m.issue21 = f.IssueFactory(project=m.project2, subject="Back to the future")

    m.wikipage11 = f.WikiPageFactory(project=m.project1)
    m.wikipage12 = f.WikiPageFactory(project=m.project1)
    m.wikipage13 = f.WikiPageFactory(project=m.project1, content="Backend to the black")
    m.wikipage14 = f.WikiPageFactory(project=m.project1, slug="Back to the black")
    m.wikipage21 = f.WikiPageFactory(project=m.project2, slug="Backend to the orange")

    return m


def test_search_all_objects_in_my_project(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project1.id})
    assert response.status_code == 200
    assert response.data["count"] == 20
    assert len(response.data["epics"]) == 4
    assert len(response.data["userstories"]) == 4
    assert len(response.data["tasks"]) == 4
    assert len(response.data["issues"]) == 4
    assert len(response.data["wikipages"]) == 4


def test_search_all_objects_in_project_is_not_mine(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project2.id})
    assert response.status_code == 200
    assert response.data["count"] == 0


def test_search_text_query_in_my_project(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": data.project1.id, "text": "future"})
    assert response.status_code == 200
    assert response.data["count"] == 12
    assert len(response.data["epics"]) == 3
    assert response.data["epics"][0]["id"] == searches_initial_data.epic11.id
    assert response.data["epics"][1]["id"] == searches_initial_data.epic12.id
    assert response.data["epics"][2]["id"] == searches_initial_data.epic14.id
    assert len(response.data["userstories"]) == 3
    assert response.data["userstories"][0]["id"] == searches_initial_data.us11.id
    assert response.data["userstories"][1]["id"] == searches_initial_data.us13.id
    assert response.data["userstories"][2]["id"] == searches_initial_data.us12.id
    assert len(response.data["tasks"]) == 3
    assert response.data["tasks"][0]["id"] == searches_initial_data.task11.id
    assert response.data["tasks"][1]["id"] == searches_initial_data.task12.id
    assert response.data["tasks"][2]["id"] == searches_initial_data.task14.id
    assert len(response.data["issues"]) == 3
    assert response.data["issues"][0]["id"] == searches_initial_data.issue14.id
    assert response.data["issues"][1]["id"] == searches_initial_data.issue12.id
    assert response.data["issues"][2]["id"] == searches_initial_data.issue11.id
    assert len(response.data["wikipages"]) == 0

    response = client.get(reverse("search-list"), {"project": data.project1.id, "text": "back"})
    assert response.status_code == 200
    assert response.data["count"] == 14
    assert len(response.data["epics"]) == 3
    assert response.data["epics"][0]["id"] == searches_initial_data.epic11.id
    assert response.data["epics"][1]["id"] == searches_initial_data.epic12.id
    assert response.data["epics"][2]["id"] == searches_initial_data.epic14.id
    assert len(response.data["userstories"]) == 3
    assert response.data["userstories"][0]["id"] == searches_initial_data.us11.id
    assert response.data["userstories"][1]["id"] == searches_initial_data.us13.id
    assert response.data["userstories"][2]["id"] == searches_initial_data.us12.id
    assert len(response.data["tasks"]) == 3
    assert response.data["tasks"][0]["id"] == searches_initial_data.task11.id
    assert response.data["tasks"][1]["id"] == searches_initial_data.task12.id
    assert response.data["tasks"][2]["id"] == searches_initial_data.task14.id
    assert len(response.data["issues"]) == 3
    assert response.data["issues"][0]["id"] == searches_initial_data.issue14.id
    assert response.data["issues"][1]["id"] == searches_initial_data.issue12.id
    assert response.data["issues"][2]["id"] == searches_initial_data.issue11.id
    # Back is a backend substring
    assert len(response.data["wikipages"]) == 2
    assert response.data["wikipages"][0]["id"] == searches_initial_data.wikipage14.id
    assert response.data["wikipages"][1]["id"] == searches_initial_data.wikipage13.id


def test_search_text_query_with_an_invalid_project_id(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": "new", "text": "future"})
    assert response.status_code == 404
