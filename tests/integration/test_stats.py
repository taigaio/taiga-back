# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from .. import factories as f
from tests.utils import disconnect_signals, reconnect_signals

from taiga.projects.services.stats import get_stats_for_project


pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.user = f.UserFactory.create()

    m.project = f.ProjectFactory(is_private=False, owner=m.user)

    m.role1 = f.RoleFactory(project=m.project)
    m.role2 = f.RoleFactory(project=m.project)

    m.null_points = f.PointsFactory(project=m.project, value=None)
    m.default_points = f.PointsFactory(project=m.project, value=0)
    m.points1 = f.PointsFactory(project=m.project, value=1)
    m.points2 = f.PointsFactory(project=m.project, value=2)
    m.points3 = f.PointsFactory(project=m.project, value=4)
    m.points4 = f.PointsFactory(project=m.project, value=8)
    m.points5 = f.PointsFactory(project=m.project, value=16)
    m.points6 = f.PointsFactory(project=m.project, value=32)

    m.open_status = f.UserStoryStatusFactory(is_closed=False)
    m.closed_status = f.UserStoryStatusFactory(is_closed=True)
    m.project.default_points = m.default_points
    m.project.save()

    m.user_story1 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone=None)
    m.user_story1.role_points.filter(role=m.role1).update(points=m.points1)

    m.user_story2 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone=None)
    m.user_story2.role_points.filter(role=m.role1).update(points=m.points2)

    m.user_story3 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone=None)
    m.user_story3.role_points.filter(role=m.role1).update(points=m.points3)

    m.user_story4 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone=None)
    m.user_story4.role_points.filter(role=m.role1).update(points=m.points4)

    # 5 and 6 are inclosed milestones
    m.user_story5 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone__closed=True,
                                       milestone__project=m.project)

    m.user_story5.role_points.filter(role=m.role1).update(points=m.points5)

    m.user_story6 = f.UserStoryFactory(project=m.project,
                                       status=m.open_status,
                                       milestone__closed=True,
                                       milestone__project=m.project)

    m.user_story6.role_points.filter(role=m.role1).update(points=m.points6)

    return m


def test_project_defined_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["defined_points_per_role"] == {data.role1.pk: 63, data.role2.pk: 0}
    data.user_story1.role_points.filter(role=data.role1).update(points=data.default_points)
    data.user_story1.role_points.filter(role=data.role2).update(points=data.points1)
    project_stats = get_stats_for_project(data.project)
    assert project_stats["defined_points_per_role"] == {data.role1.pk: 62, data.role2.pk: 1}


def test_project_closed_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {}
    data.user_story1.is_closed = True
    data.user_story1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 1, data.role2.pk: 0}
    data.user_story2.is_closed = True
    data.user_story2.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 3, data.role2.pk: 0}
    data.user_story3.is_closed = True
    data.user_story3.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 7, data.role2.pk: 0}
    data.user_story4.is_closed = True
    data.user_story4.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 15, data.role2.pk: 0}
    data.user_story5.is_closed = True
    data.user_story5.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 31, data.role2.pk: 0}
    data.user_story6.is_closed = True
    data.user_story6.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 63, data.role2.pk: 0}

    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points"] == 63
    assert project_stats["speed"] == 24


def test_project_assigned_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 48, data.role2.pk: 0}
    data.user_story1.milestone = data.user_story6.milestone
    data.user_story1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 49, data.role2.pk: 0}
    data.user_story2.milestone = data.user_story6.milestone
    data.user_story2.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 51, data.role2.pk: 0}
    data.user_story3.milestone = data.user_story6.milestone
    data.user_story3.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 55, data.role2.pk: 0}
    data.user_story4.milestone = data.user_story6.milestone
    data.user_story4.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 63, data.role2.pk: 0}
