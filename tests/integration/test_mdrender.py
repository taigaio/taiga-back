# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from taiga.mdrender.service import render, render_and_extract

from unittest.mock import MagicMock

from .. import factories

pytestmark = pytest.mark.django_db

dummy_project = MagicMock()
dummy_project.id = 1
dummy_project.slug = "test"

def test_proccessor_valid_user_mention():
    user=factories.UserFactory(username="user1", full_name="test name")
    project=factories.ProjectFactory()
    factories.MembershipFactory(user=user, project=project)
    result = render(project, "**@user1**")
    expected_result = "<p><strong><a class=\"mention\" href=\"http://localhost:9001/profile/user1\" title=\"test name\">@user1</a></strong></p>"
    assert result == expected_result


def test_proccessor_valid_user_mention_with_dashes():
    user=factories.UserFactory(username="user1_text_after_dash", full_name="test name")
    project=factories.ProjectFactory()
    factories.MembershipFactory(user=user, project=project)
    result = render(project, "**@user1_text_after_dash**")
    expected_result = "<p><strong><a class=\"mention\" href=\"http://localhost:9001/profile/user1_text_after_dash\" title=\"test name\">@user1_text_after_dash</a></strong></p>"
    assert result == expected_result


def test_proccessor_invalid_user_mention():
    result = render(dummy_project, "**@notvaliduser**")
    assert result == '<p><strong>@notvaliduser</strong></p>'


def test_render_and_extract_mentions():
    user=factories.UserFactory(username="user1", full_name="test name")
    project=factories.ProjectFactory()
    factories.MembershipFactory(user=user, project=project)
    (_, extracted) = render_and_extract(project, "**@user1**")
    assert extracted['mentions'] == [user]

def test_render_and_extract_mentions_with_capitalized_username():
    user=factories.UserFactory(username="User1", full_name="test")
    project=factories.ProjectFactory()
    factories.MembershipFactory(user=user, project=project)
    (_, extracted) = render_and_extract(project, "**@User1**")
    assert extracted['mentions'] == [user]


def test_proccessor_valid_email():
    result = render(dummy_project, "**beta.tester@taiga.io**")
    expected_result = "<p><strong><a href=\"mailto:beta.tester@taiga.io\" target=\"_blank\">beta.tester@taiga.io</a></strong></p>"
    assert result == expected_result
