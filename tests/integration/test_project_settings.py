# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

import json

import pytest

from django.apps import apps
from django.urls import reverse

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


def test_retrieve_homepage_setting_with_allowed_sections(client):
    # Default template has next configuration:
    # "is_epics_activated": false,
    # "is_backlog_activated": true,
    # "is_kanban_activated": false,
    # "is_wiki_activated": true,
    # "is_issues_activated": true,
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(user=user, project=project, is_admin=False)
    membership.role.permissions = ["view_us", "view_wiki_pages"]
    membership.role.save()
    url = reverse("user-project-settings-list")

    client.login(project.owner)

    response = client.get(url)

    assert response.status_code == 200
    assert 1 == len(response.data)
    assert 1 == response.data[0].get("homepage")
    assert 3 == len(response.data[0].get("allowed_sections"))

    assert Section.timeline in response.data[0].get("allowed_sections")
    assert Section.backlog in response.data[0].get("allowed_sections")
    assert Section.wiki in response.data[0].get("allowed_sections")

    assert Section.epics not in response.data[0].get("allowed_sections")
    assert Section.issues not in response.data[0].get("allowed_sections")


def test_avoid_patch_homepage_setting_with_not_allowed_section(client):
    # Default template has next configuration:
    # "is_epics_activated": false,
    # "is_backlog_activated": true,
    # "is_kanban_activated": false,
    # "is_wiki_activated": true,
    # "is_issues_activated": true,
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(user=user, project=project,
                                            is_admin=False)
    membership.role.permissions = ["view_us", "view_wiki_pages"]
    membership.role.save()

    setting = services.create_user_project_settings_if_not_exists(project,
                                                                  project.owner)

    url = reverse("user-project-settings-detail", args=[setting.pk])

    client.login(project.owner)
    response = client.json.patch(url, data=json.dumps({"homepage": Section.backlog}))
    assert response.status_code == 200

    response = client.json.patch(url, data=json.dumps({"homepage": Section.issues}))
    assert response.status_code == 400
