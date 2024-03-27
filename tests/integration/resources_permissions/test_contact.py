# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.urls import reverse

from tests import factories as f
from tests.utils import helper_test_http_method

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.user = f.UserFactory.create()
    m.project = f.ProjectFactory.create(is_private=False)
    f.MembershipFactory(user=m.project.owner, project=m.project, is_admin=True)

    return m


def test_contact_create(client, data):
    url = reverse("contact-list")
    users = [None, data.user]

    contact_data = json.dumps({
        "project": data.project.id,
        "comment": "Testing comment"
    })
    results = helper_test_http_method(client, 'post', url, contact_data, users)
    assert results == [401, 201]
