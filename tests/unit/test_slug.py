# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.contrib.auth import get_user_model

from taiga.projects.models import Project
from taiga.base.utils.slug import slugify

from tests.utils import disconnect_signals, reconnect_signals


def setup_module():
    disconnect_signals()


def teardown_module():
    reconnect_signals()


def test_slugify_1():
    assert slugify("漢字") == "han-zi"


def test_slugify_2():
    assert slugify("TestExamplePage") == "testexamplepage"


def test_slugify_3():
    assert slugify(None) == ""


@pytest.mark.django_db
def test_project_slug_with_special_chars():
    user = get_user_model().objects.create(username="test")
    project = Project.objects.create(name="漢字", description="漢字", owner=user)
    project.save()

    assert project.slug == "test-han-zi"


@pytest.mark.django_db
def test_project_with_existing_name_slug_with_special_chars():
    user = get_user_model().objects.create(username="test")
    Project.objects.create(name="漢字", description="漢字", owner=user)
    project = Project.objects.create(name="漢字", description="漢字", owner=user)

    assert project.slug == "test-han-zi-1"
