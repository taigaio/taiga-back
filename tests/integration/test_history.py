# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
from unittest.mock import MagicMock
from unittest.mock import patch

from django.core.urlresolvers import reverse
from .. import factories as f

from taiga.projects.history import services
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType


pytestmark = pytest.mark.django_db


def test_take_snapshot_crete():
    issue = f.IssueFactory.create()

    qs_all = HistoryEntry.objects.all()
    qs_created = qs_all.filter(type=HistoryType.create)

    assert qs_all.count() == 0

    services.take_snapshot(issue, user=issue.owner)

    assert qs_all.count() == 1
    assert qs_created.count() == 1


def test_take_two_snapshots_with_changes():
    issue = f.IssueFactory.create()

    qs_all = HistoryEntry.objects.all()
    qs_created = qs_all.filter(type=HistoryType.create)
    qs_hidden = qs_all.filter(is_hidden=True)

    assert qs_all.count() == 0

    # Two snapshots with modification should
    # generate two snapshots.
    services.take_snapshot(issue, user=issue.owner)
    issue.description = "foo1"
    issue.save()
    services.take_snapshot(issue, user=issue.owner)
    assert qs_all.count() == 2
    assert qs_created.count() == 1
    assert qs_hidden.count() == 0


def test_take_two_snapshots_without_changes():
    issue = f.IssueFactory.create()

    qs_all = HistoryEntry.objects.all()
    qs_created = qs_all.filter(type=HistoryType.create)
    qs_hidden = qs_all.filter(is_hidden=True)

    assert qs_all.count() == 0

    # Two snapshots without modifications only
    # generate one unique snapshot.
    services.take_snapshot(issue, user=issue.owner)
    services.take_snapshot(issue, user=issue.owner)

    assert qs_all.count() == 1
    assert qs_created.count() == 1
    assert qs_hidden.count() == 0

def test_take_snapshot_from_deleted_object():
    issue = f.IssueFactory.create()

    qs_all = HistoryEntry.objects.all()
    qs_deleted = qs_all.filter(type=HistoryType.delete)

    assert qs_all.count() == 0

    services.take_snapshot(issue, user=issue.owner, delete=True)

    assert qs_all.count() == 1
    assert qs_deleted.count() == 1


def test_real_snapshot_frequency(settings):
    settings.MAX_PARTIAL_DIFFS = 2

    issue = f.IssueFactory.create()
    counter = 0

    qs_all = HistoryEntry.objects.all()
    qs_snapshots = qs_all.filter(is_snapshot=True)
    qs_partials = qs_all.filter(is_snapshot=False)

    assert qs_all.count() == 0
    assert qs_snapshots.count() == 0
    assert qs_partials.count() == 0

    def _make_change():
        nonlocal counter
        issue.description = "desc{}".format(counter)
        issue.save()
        services.take_snapshot(issue, user=issue.owner)
        counter += 1

    _make_change()
    assert qs_all.count() == 1
    assert qs_snapshots.count() == 1
    assert qs_partials.count() == 0

    _make_change()
    assert qs_all.count() == 2
    assert qs_snapshots.count() == 1
    assert qs_partials.count() == 1

    _make_change()
    assert qs_all.count() == 3
    assert qs_snapshots.count() == 1
    assert qs_partials.count() == 2

    _make_change()
    assert qs_all.count() == 4
    assert qs_snapshots.count() == 2
    assert qs_partials.count() == 2


def test_issue_resource_history_test(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    member = f.MembershipFactory.create(project=project, user=user, role=role)
    issue = f.IssueFactory.create(owner=user, project=project)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    url = reverse("issues-detail", args=[issue.pk])

    client.login(user)

    qs_all = HistoryEntry.objects.all()
    qs_deleted = qs_all.filter(type=HistoryType.delete)
    qs_changed = qs_all.filter(type=HistoryType.change)
    qs_created = qs_all.filter(type=HistoryType.create)

    assert qs_all.count() == 0

    with patch(mock_path) as m:
        data = {"subject": "Fooooo", "version": issue.version}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

    assert qs_all.count() == 1
    assert qs_created.count() == 1
    assert qs_changed.count() == 0
    assert qs_deleted.count() == 0

    with patch(mock_path) as m:
        response = client.delete(url)
        assert response.status_code == 204

    assert qs_all.count() == 2
    assert qs_created.count() == 1
    assert qs_changed.count() == 0
    assert qs_deleted.count() == 1


def test_take_hidden_snapshot():
    task = f.TaskFactory.create()

    qs_all = HistoryEntry.objects.all()
    qs_hidden = qs_all.filter(is_hidden=True)

    assert qs_all.count() == 0

    # Two snapshots with modification should
    # generate two snapshots.
    services.take_snapshot(task, user=task.owner)
    task.us_order = 3
    task.save()

    services.take_snapshot(task, user=task.owner)
    assert qs_all.count() == 2
    assert qs_hidden.count() == 1


def test_history_with_only_comment_shouldnot_be_hidden(client):
    project = f.create_project()
    us = f.create_userstory(project=project)

    qs_all = HistoryEntry.objects.all()
    qs_hidden = qs_all.filter(is_hidden=True)

    assert qs_all.count() == 0

    url = reverse("userstories-detail", args=[us.pk])
    data = json.dumps({"comment": "test comment", "version": us.version})

    print(url, data)
    client.login(project.owner)
    response = client.patch(url, data, content_type="application/json")

    assert response.status_code == 200, response.content
    assert qs_all.count() == 1
    assert qs_hidden.count() == 0

