import pytest

from django.apps import apps

from .. import factories as f

from taiga.projects.settings import services
from taiga.projects.settings.choices import Section

pytestmark = pytest.mark.django_db


def test_home_page_setting_existence():
    project = f.ProjectFactory.create()
    assert not services.user_project_settings_exists(project, project.owner)

    services.create_user_project_settings(project, project.owner, Section.kanban)
    assert services.user_project_settings_exists(project, project.owner)


def test_create_retrieve_home_page_setting():
    project = f.ProjectFactory.create()

    policy_model_cls = apps.get_model("settings", "UserProjectSettings")
    current_number = policy_model_cls.objects.all().count()
    assert current_number == 0

    setting = services.create_user_project_settings_if_not_exists(project,
                                                                  project.owner)

    current_number = policy_model_cls.objects.all().count()
    assert current_number == 1
    assert setting.homepage == Section.timeline
