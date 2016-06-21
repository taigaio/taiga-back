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

from django.core.urlresolvers import reverse

from tests import factories as f

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return f.UserFactory.create()


def test_create_feedback(client, user):
    url = reverse("feedback-list")

    feedback_data = {"comment": "One feedback comment"}
    feedback_data = json.dumps(feedback_data)

    client.login(user)

    response = client.post(url, feedback_data, content_type="application/json")
    assert response.status_code == 200

    assert response.data.get("id", None)
    assert response.data.get("created_date", None)
    assert response.data.get("full_name", user.full_name)
    assert response.data.get("email", user.email)

    client.logout()


def test_create_feedback_without_comments(client, user):
    url = reverse("feedback-list")

    feedback_data = json.dumps({})

    client.login(user)

    response = client.post(url, feedback_data, content_type="application/json")
    assert response.status_code == 400
    assert response.data.get("comment", None)

    client.logout()
