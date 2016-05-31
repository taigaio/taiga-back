# -*- coding: utf-8 -*-
import pytest

from .. import factories as f
from ..utils import disconnect_signals, reconnect_signals


def setup_module():
    disconnect_signals()


def teardown_module():
    reconnect_signals()


pytestmark = pytest.mark.django_db


def test_project_update_role_points():
    """Test that relation to project roles are created for stories not related to those roles.

    The "relation" is just a mere `RolePoints` relation between the story and the role with
    points set to the project's null-point.
    """
    project = f.ProjectFactory.create()
    related_role = f.RoleFactory.create(project=project, computable=True)
    not_related_role = f.RoleFactory.create(project=project, computable=True)
    null_points = f.PointsFactory.create(project=project, value=None)
    user_story = f.UserStoryFactory(project=project)
    user_story.role_points.add(f.RolePointsFactory(role=related_role, points=null_points))

    project.update_role_points()

    assert user_story.role_points.filter(role=not_related_role, points=null_points).count() == 1
