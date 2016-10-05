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
from unittest.mock import patch
from unittest.mock import Mock

from taiga.base.utils import json

from .. import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.project_owner = f.UserFactory.create()

    m.project1 = f.ProjectFactory(is_private=True,
                                  anon_permissions=[],
                                  public_permissions=[],
                                  owner=m.project_owner)
    f.MembershipFactory(project=m.project1,
                        user=m.project_owner,
                        is_admin=True)
    m.webhook1 = f.WebhookFactory(project=m.project1)
    m.webhooklog1 = f.WebhookLogFactory(webhook=m.webhook1)

    return m


def test_webhook_action_test_transform_to_json(client, data):
    url = reverse('webhooks-test', kwargs={"pk": data.webhook1.pk})

    response = Mock(status_code=200, headers={}, text="ok")
    response.elapsed.total_seconds.return_value = 100

    with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
        client.login(data.project_owner)
        response = client.json.post(url)
        assert response.status_code == 200
        assert json.loads(response.data["response_data"]) == {"content": "ok"}
