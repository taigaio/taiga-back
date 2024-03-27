# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.urls import reverse
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

    with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response), \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            client.login(data.project_owner)
            response = client.json.post(url)
            assert response.status_code == 200
            assert json.loads(response.data["response_data"]) == {"content": "ok"}
