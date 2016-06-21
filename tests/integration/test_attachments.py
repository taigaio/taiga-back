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

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_create_user_story_attachment_without_file(client):
    """
    Bug test "Don't create attachments without attached_file"
    """
    us = f.UserStoryFactory.create()
    f.MembershipFactory(project=us.project, user=us.owner, is_admin=True)
    attachment_data = {
        "description": "test",
        "attached_file": None,
        "project": us.project_id,
    }

    url = reverse('userstory-attachments-list')

    client.login(us.owner)
    response = client.post(url, attachment_data)
    assert response.status_code == 400


def test_create_attachment_on_wrong_project(client):
    issue1 = f.create_issue()
    issue2 = f.create_issue(owner=issue1.owner)
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_admin=True)

    assert issue1.owner == issue2.owner
    assert issue1.project.owner == issue2.project.owner

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue2.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile("test.txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.status_code == 400


def test_create_attachment_with_long_file_name(client):
    issue1 = f.create_issue()
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_admin=True)

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue1.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile(500*"x"+".txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.data["attached_file"].endswith("/"+100*"x"+".txt")
