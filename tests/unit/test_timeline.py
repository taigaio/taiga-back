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

from unittest.mock import patch, call

from django.contrib.auth import get_user_model

from taiga.timeline import service
from taiga.timeline.models import Timeline
from taiga.projects.models import Project

import pytest


def test_push_to_timeline_many_objects():
    with patch("taiga.timeline.service._add_to_object_timeline") as mock:
        users = [get_user_model(), get_user_model(), get_user_model()]
        project = Project()
        service.push_to_timeline(users, project, "test", project.created_date)
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], project, "test", project.created_date, "default", {}),
            call(users[1], project, "test", project.created_date, "default", {}),
            call(users[2], project, "test", project.created_date, "default", {}),
        ]
        with pytest.raises(Exception):
            service.push_to_timeline(None, project, "test")


def test_add_to_objects_timeline():
    with patch("taiga.timeline.service._add_to_object_timeline") as mock:
        users = [get_user_model(), get_user_model(), get_user_model()]
        project = Project()
        service._add_to_objects_timeline(users, project, "test", project.created_date)
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], project, "test", project.created_date, "default", {}),
            call(users[1], project, "test", project.created_date, "default", {}),
            call(users[2], project, "test", project.created_date, "default", {}),
        ]
        with pytest.raises(Exception):
            service.push_to_timeline(None, project, "test")


def test_get_impl_key_from_model():
    assert service._get_impl_key_from_model(Timeline, "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_get_impl_key_from_typename():
    assert service._get_impl_key_from_typename("timeline.timeline", "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_register_timeline_implementation():
    test_func = lambda x: "test-func-result"
    service.register_timeline_implementation("timeline.timeline", "test", test_func)
    assert service._timeline_impl_map["timeline.timeline.test"](None) == "test-func-result"

    @service.register_timeline_implementation("timeline.timeline", "test-decorator")
    def decorated_test_function(x):
        return "test-decorated-func-result"

    assert service._timeline_impl_map["timeline.timeline.test-decorator"](None) == "test-decorated-func-result"
