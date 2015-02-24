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

from .. import factories

from taiga.timeline import service
from taiga.timeline.models import Timeline


pytestmark = pytest.mark.django_db


def test_add_to_object_timeline():
    Timeline.objects.all().delete()
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()

    service.register_timeline_implementation("users.user", "test", lambda x, extra_data=None: str(id(x)))

    service._add_to_object_timeline(user1, user2, "test")

    assert Timeline.objects.filter(object_id=user1.id).count() == 1
    assert Timeline.objects.order_by("-id")[0].data == id(user2)


def test_get_timeline():
    Timeline.objects.all().delete()

    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    user3 = factories.UserFactory()
    user4 = factories.UserFactory()

    service.register_timeline_implementation("users.user", "test", lambda x, extra_data=None: str(id(x)))

    service._add_to_object_timeline(user1, user1, "test")
    service._add_to_object_timeline(user1, user2, "test")
    service._add_to_object_timeline(user1, user3, "test")
    service._add_to_object_timeline(user1, user4, "test")

    service._add_to_object_timeline(user2, user1, "test")

    assert service.get_timeline(user1).count() == 4
    assert service.get_timeline(user2).count() == 1
    assert service.get_timeline(user3).count() == 0
