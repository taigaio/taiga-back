# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
import json

from django.core.urlresolvers import reverse
from .. import factories as f


pytestmark = pytest.mark.django_db


def test_archived_filter(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user)
    f.UserStoryFactory.create(project=project)
    f.UserStoryFactory.create(is_archived=True, project=project)

    client.login(user)

    url = reverse("userstories-list")

    data = {}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 2

    data = {"is_archived": 0}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 1

    data = {"is_archived": 1}
    response = client.get(url, data)
    assert len(json.loads(response.content.decode('utf-8'))) == 1
