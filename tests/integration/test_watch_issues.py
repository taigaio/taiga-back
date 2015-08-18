# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2015 Anler Hernández <hello@anler.me>
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

pytestmark = pytest.mark.django_db


def test_watch_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_owner=True)
    url = reverse("issues-watch", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_owner=True)
    url = reverse("issues-watch", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200
