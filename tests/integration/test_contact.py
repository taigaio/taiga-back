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

from django.core import mail
from django.core.urlresolvers import reverse

from tests import factories as f

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


def test_create_comment(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)

    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    assert len(mail.outbox) == 0
    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [project.owner.email]



def test_create_comment_disabled(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    project.is_contact_activated = False
    project.save()
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)

    url = reverse("contact-list")

    contact_data = json.dumps({
        "project": project.id,
        "comment": "Testing comment"
    })

    client.login(user)

    response = client.post(url, contact_data, content_type="application/json")
    assert response.status_code == 403
