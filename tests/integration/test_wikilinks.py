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

from django.core.urlresolvers import reverse
from django.core import mail

from taiga.base.utils import json
from taiga.projects.notifications.choices import NotifyLevel

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_create_wiki_link_of_existent_wiki_page_with_permissions(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_wiki_pages', 'view_wiki_link',
                                                              'add_wiki_page', 'add_wiki_link'])

    f.MembershipFactory.create(project=project, user=project.owner, role=role)
    project.owner.notify_policies.filter(project=project).update(notify_level=NotifyLevel.all)

    user = f.UserFactory.create()
    f.MembershipFactory.create(project=project, user=user, role=role)

    wiki_page = f.WikiPageFactory.create(project=project, owner=user, slug="test", content="test content")

    mail.outbox = []

    url = reverse("wiki-links-list")

    data = {
        "title": "test",
        "href": "test",
        "project": project.pk,
    }

    assert project.wiki_pages.all().count() == 1
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(mail.outbox) == 0
    assert project.wiki_pages.all().count() == 1


def test_create_wiki_link_of_inexistent_wiki_page_with_permissions(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_wiki_pages', 'view_wiki_link',
                                                              'add_wiki_page', 'add_wiki_link'])

    f.MembershipFactory.create(project=project, user=project.owner, role=role)
    project.owner.notify_policies.filter(project=project).update(notify_level=NotifyLevel.all)

    user = f.UserFactory.create()
    f.MembershipFactory.create(project=project, user=user, role=role)

    mail.outbox = []

    url = reverse("wiki-links-list")

    data = {
        "title": "test",
        "href": "test",
        "project": project.pk,
    }

    assert project.wiki_pages.all().count() == 0
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert project.wiki_pages.all().count() == 1


def test_create_wiki_link_of_inexistent_wiki_page_without_permissions(client):
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=['view_wiki_pages', 'view_wiki_link',
                                                              'add_wiki_link'])

    f.MembershipFactory.create(project=project, user=project.owner, role=role)
    project.owner.notify_policies.filter(project=project).update(notify_level=NotifyLevel.all)

    user = f.UserFactory.create()
    f.MembershipFactory.create(project=project, user=user, role=role)

    mail.outbox = []

    url = reverse("wiki-links-list")

    data = {
        "title": "test",
        "href": "test",
        "project": project.pk,
    }

    assert project.wiki_pages.all().count() == 0
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(mail.outbox) == 0
    assert project.wiki_pages.all().count() == 0
