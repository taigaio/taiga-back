from unittest.mock import patch, MagicMock, call

from django.core.exceptions import ValidationError

from taiga.timeline import service
from taiga.timeline.models import Timeline
from taiga.projects.models import Project
from taiga.users.models import User

import pytest


def test_push_to_timeline_many_objects():
    with patch("taiga.timeline.service._add_to_object_timeline") as mock:
        users = [User(), User(), User()]
        project = Project()
        service.push_to_timeline(users, project, "test")
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], project, "test", "default", {}),
            call(users[1], project, "test", "default", {}),
            call(users[2], project, "test", "default", {}),
        ]
        with pytest.raises(Exception):
            service.push_to_timeline(None, project, "test")

def test_add_to_objects_timeline():
    with patch("taiga.timeline.service._add_to_object_timeline") as mock:
        users = [User(), User(), User()]
        project = Project()
        service._add_to_objects_timeline(users, project, "test")
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], project, "test", "default", {}),
            call(users[1], project, "test", "default", {}),
            call(users[2], project, "test", "default", {}),
        ]
        with pytest.raises(Exception):
            service.push_to_timeline(None, project, "test")


def test_modify_created_timeline_entry():
    timeline = Timeline()
    timeline.pk = 3
    with pytest.raises(ValidationError):
        timeline.save()


def test_get_impl_key_from_model():
    assert service._get_impl_key_from_model(Timeline, "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_get_impl_key_from_typename():
    assert service._get_impl_key_from_typename("timeline.timeline", "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_get_class_implementation():
    service._timeline_impl_map["timeline.timeline.test"] = "test"
    assert service._get_class_implementation(Timeline, "test") == "test"
    assert service._get_class_implementation(Timeline, "other") == None


def test_register_timeline_implementation():
    test_func = lambda x: "test-func-result"
    service.register_timeline_implementation("timeline.timeline", "test", test_func)
    assert service._timeline_impl_map["timeline.timeline.test"](None) == "test-func-result"

    @service.register_timeline_implementation("timeline.timeline", "test-decorator")
    def decorated_test_function(x):
        return "test-decorated-func-result"

    assert service._timeline_impl_map["timeline.timeline.test-decorator"](None) == "test-decorated-func-result"
