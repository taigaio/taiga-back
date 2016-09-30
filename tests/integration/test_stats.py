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
    m.points1 = f.PointsFactory(project=m.project, value=1)
    m.points2 = f.PointsFactory(project=m.project, value=2)
    m.points3 = f.PointsFactory(project=m.project, value=4)
    m.points4 = f.PointsFactory(project=m.project, value=8)
    m.points5 = f.PointsFactory(project=m.project, value=16)
    m.points6 = f.PointsFactory(project=m.project, value=32)

    m.open_status = f.UserStoryStatusFactory(is_closed=False)
    m.closed_status = f.UserStoryStatusFactory(is_closed=True)

    m.role_points1 = f.RolePointsFactory(role=m.role1,
                                         points=m.points1,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone=None)
    m.role_points2 = f.RolePointsFactory(role=m.role1,
                                         points=m.points2,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone=None)
    m.role_points3 = f.RolePointsFactory(role=m.role1,
                                         points=m.points3,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone=None)
    m.role_points4 = f.RolePointsFactory(role=m.project.roles.all()[0],
                                         points=m.points4,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone=None)
    # 5 and 6 are in closed milestones
    m.role_points5 = f.RolePointsFactory(role=m.project.roles.all()[0],
                                         points=m.points5,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone__closed=True,
                                         user_story__milestone__project=m.project)
    m.role_points6 = f.RolePointsFactory(role=m.project.roles.all()[0],
                                         points=m.points6,
                                         user_story__project=m.project,
                                         user_story__status=m.open_status,
                                         user_story__milestone__closed=True,
                                         user_story__milestone__project=m.project)

    m.user_story1 = m.role_points1.user_story
    m.user_story2 = m.role_points2.user_story
    m.user_story3 = m.role_points3.user_story
    m.user_story4 = m.role_points4.user_story
    m.user_story5 = m.role_points5.user_story
    m.user_story6 = m.role_points6.user_story

    m.milestone = f.MilestoneFactory(project=m.project)

    return m


def test_project_defined_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["defined_points_per_role"] == {data.role1.pk: 63}
    data.role_points1.role = data.role2
    data.role_points1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["defined_points_per_role"] == {data.role1.pk: 62, data.role2.pk: 1}


def test_project_closed_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {}
    data.role_points1.role = data.role2
    data.role_points1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {}
    data.user_story1.is_closed = True
    data.user_story1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role2.pk: 1}
    data.user_story2.is_closed = True
    data.user_story2.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 2, data.role2.pk: 1}
    data.user_story3.is_closed = True
    data.user_story3.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 6, data.role2.pk: 1}
    data.user_story4.is_closed = True
    data.user_story4.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 14, data.role2.pk: 1}

    data.user_story5.is_closed = True
    data.user_story5.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 30, data.role2.pk: 1}
    data.user_story6.is_closed = True
    data.user_story6.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points_per_role"] == {data.role1.pk: 62, data.role2.pk: 1}

    project_stats = get_stats_for_project(data.project)
    assert project_stats["closed_points"] == 63
    assert project_stats["speed"] == 24


def test_project_assigned_points(client, data):
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 48}
    data.role_points1.role = data.role2
    data.role_points1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 48}
    data.user_story1.milestone = data.milestone
    data.user_story1.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 48, data.role2.pk: 1}
    data.user_story2.milestone = data.milestone
    data.user_story2.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 50, data.role2.pk: 1}
    data.user_story3.milestone = data.milestone
    data.user_story3.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 54, data.role2.pk: 1}
    data.user_story4.milestone = data.milestone
    data.user_story4.save()
    project_stats = get_stats_for_project(data.project)
    assert project_stats["assigned_points_per_role"] == {data.role1.pk: 62, data.role2.pk: 1}
