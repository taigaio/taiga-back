from unittest import mock

from taiga.projects.stars import services as stars
from .. import factories as f


def setup_module(module):
    module.patcher = mock.patch.object(stars, "atomic", mock.MagicMock())
    module.patcher.start()

def teardown_module(module):
    module.patcher.stop()


def test_user_star_project():
    "An user can star a project"
    user = f.UserFactory.build()
    project = f.ProjectFactory.build()

    with mock.patch("taiga.projects.stars.services.Fan") as Fan:
        with mock.patch("taiga.projects.stars.services.Stars") as Stars:
            stars_instance = mock.Mock()

            Fan.objects.get_or_create = mock.MagicMock(return_value=(mock.Mock(), True))
            Stars.objects.get_or_create = mock.MagicMock(return_value=(stars_instance, True))

            stars.star(project, user=user)

            assert stars_instance.count.connector == '+'
            assert stars_instance.count.children[1] == 1
            assert stars_instance.save.called


def test_idempotence_user_star_project():
    "An user can star a project many times but only one star is counted"
    user = f.UserFactory.build()
    project = f.ProjectFactory.build()

    with mock.patch("taiga.projects.stars.services.Fan") as Fan:
        with mock.patch("taiga.projects.stars.services.Stars") as Stars:
            stars_instance = mock.Mock()

            Fan.objects.get_or_create = mock.MagicMock(return_value=(mock.Mock(), False))
            Stars.objects.get_or_create = mock.MagicMock(return_value=(stars_instance, True))

            stars.star(project, user=user)

            assert not Fan.objects.create.called
            assert not stars_instance.save.called


def test_user_unstar_project():
    "An user can unstar a project"
    fan = f.FanFactory.build()

    with mock.patch("taiga.projects.stars.services.Fan") as Fan:
        with mock.patch("taiga.projects.stars.services.Stars") as Stars:
            delete_mock = mock.Mock()
            stars_instance = mock.Mock()

            Fan.objects.filter(project=fan.project, user=fan.user).exists = mock.Mock(
                return_value=True)
            Fan.objects.filter(project=fan.project, user=fan.user).delete = delete_mock
            Stars.objects.get_or_create = mock.MagicMock(return_value=(stars_instance, True))

            stars.unstar(fan.project, user=fan.user)

            assert delete_mock.called
            assert stars_instance.count.connector == '-'
            assert stars_instance.count.children[1] == 1
            assert stars_instance.save.called


def test_idempotence_user_unstar_project():
    "An user can unstar a project many times but only one star is discounted"
    fan = f.FanFactory.build()

    with mock.patch("taiga.projects.stars.services.Fan") as Fan:
        with mock.patch("taiga.projects.stars.services.Stars") as Stars:
            delete_mock = mock.Mock()
            stars_instance = mock.Mock()

            Fan.objects.filter(project=fan.project, user=fan.user).exists = mock.Mock(
                return_value=False)
            Fan.objects.filter(project=fan.project, user=fan.user).delete = delete_mock
            Stars.objects.get_or_create = mock.MagicMock(return_value=(stars_instance, True))

            stars.unstar(fan.project, user=fan.user)

            assert not delete_mock.called
            assert not stars_instance.save.called
