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

from taiga.permissions.permissions import MEMBERS_PERMISSIONS
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

    f.RoleFactory(project=m.project2)

    m.points1 = f.PointsFactory(project=m.project1, value=None)
    m.points2 = f.PointsFactory(project=m.project2, value=None)

    m.role_points1 = f.RolePointsFactory.create(role=m.project1.roles.all()[0],
                                                points=m.points1,
                                                user_story__project=m.project1)
    m.role_points2 = f.RolePointsFactory.create(role=m.project1.roles.all()[0],
                                                points=m.points1,
                                                user_story__project=m.project1,
                                                user_story__description="Back to the future")
    m.role_points3 = f.RolePointsFactory.create(role=m.project2.roles.all()[0],
                                                points=m.points2,
                                                user_story__project=m.project2)

    m.us1 = m.role_points1.user_story
    m.us2 = m.role_points2.user_story
    m.us3 = m.role_points3.user_story

    m.tsk1 = f.TaskFactory.create(project=m.project2)
    m.tsk2 = f.TaskFactory.create(project=m.project1)
    m.tsk3 = f.TaskFactory.create(project=m.project1, subject="Back to the future")

    m.iss1 = f.IssueFactory.create(project=m.project1, subject="Backend and Frontend")
    m.iss2 = f.IssueFactory.create(project=m.project2)
    m.iss3 = f.IssueFactory.create(project=m.project1)

    m.wiki1 = f.WikiPageFactory.create(project=m.project1)
    m.wiki2 = f.WikiPageFactory.create(project=m.project1, content="Frontend, future")
    m.wiki3 = f.WikiPageFactory.create(project=m.project2)

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
    assert response.status_code == 200
    assert response.data["count"] == 0


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
    assert response.data["count"] == 3
    assert len(response.data["userstories"]) == 1
    assert len(response.data["tasks"]) == 1
    # Back is a backend substring
    assert len(response.data["issues"]) == 1
    assert len(response.data["wikipages"]) == 0


def test_search_text_query_with_an_invalid_project_id(client, searches_initial_data):
    data = searches_initial_data

    client.login(data.member1.user)

    response = client.get(reverse("search-list"), {"project": "new", "text": "future"})
    assert response.status_code == 404
