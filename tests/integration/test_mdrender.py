import pytest

from taiga.mdrender.service import render, render_and_extract

from unittest.mock import MagicMock

from .. import factories

pytestmark = pytest.mark.django_db

dummy_project = MagicMock()
dummy_project.id = 1
dummy_project.slug = "test"


def test_proccessor_valid_user_mention():
    factories.UserFactory(username="user1", first_name="test", last_name="name")
    result = render(dummy_project, "**@user1**")
    expected_result = "<p><strong><a alt=\"test name\" class=\"mention\" href=\"/#/profile/user1\" title=\"test name\">&commat;user1</a></strong></p>"
    assert result == expected_result


def test_proccessor_invalid_user_mention():
    result = render(dummy_project, "**@notvaliduser**")
    assert result == '<p><strong>@notvaliduser</strong></p>'


def test_render_and_extract_mentions():
    user = factories.UserFactory(username="user1", first_name="test", last_name="name")
    (_, extracted) = render_and_extract(dummy_project, "**@user1**")
    assert extracted['mentions'] == [user]
