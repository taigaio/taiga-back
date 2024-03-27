# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.urls import reverse
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
