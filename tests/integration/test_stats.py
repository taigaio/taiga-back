import pytest

from .. import factories as f
from tests.utils import disconnect_signals, reconnect_signals

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

    m.user_story1 = m.role_points1.user_story
    m.user_story2 = m.role_points2.user_story
    m.user_story3 = m.role_points3.user_story
    m.user_story4 = m.role_points4.user_story

    m.milestone = f.MilestoneFactory(project=m.project)

    return m


def test_project_defined_points(client, data):
    assert data.project.defined_points == {data.role1.pk: 15}
    data.role_points1.role = data.role2
    data.role_points1.save()
    assert data.project.defined_points == {data.role1.pk: 14, data.role2.pk: 1}


def test_project_closed_points(client, data):
    assert data.project.closed_points == {}
    data.role_points1.role = data.role2
    data.role_points1.save()
    assert data.project.closed_points == {}
    data.user_story1.is_closed = True
    data.user_story1.save()
    assert data.project.closed_points == {data.role2.pk: 1}
    data.user_story2.is_closed = True
    data.user_story2.save()
    assert data.project.closed_points == {data.role1.pk: 2, data.role2.pk: 1}
    data.user_story3.is_closed = True
    data.user_story3.save()
    assert data.project.closed_points == {data.role1.pk: 6, data.role2.pk: 1}
    data.user_story4.is_closed = True
    data.user_story4.save()
    assert data.project.closed_points == {data.role1.pk: 14, data.role2.pk: 1}


def test_project_assigned_points(client, data):
    assert data.project.assigned_points == {}
    data.role_points1.role = data.role2
    data.role_points1.save()
    assert data.project.assigned_points == {}
    data.user_story1.milestone = data.milestone
    data.user_story1.save()
    assert data.project.assigned_points == {data.role2.pk: 1}
    data.user_story2.milestone = data.milestone
    data.user_story2.save()
    assert data.project.assigned_points == {data.role1.pk: 2, data.role2.pk: 1}
    data.user_story3.milestone = data.milestone
    data.user_story3.save()
    assert data.project.assigned_points == {data.role1.pk: 6, data.role2.pk: 1}
    data.user_story4.milestone = data.milestone
    data.user_story4.save()
    assert data.project.assigned_points == {data.role1.pk: 14, data.role2.pk: 1}
