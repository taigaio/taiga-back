# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Taiga Agile LLC <taiga@taiga.io>
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

import datetime

from .. import factories as f

from taiga.projects.history.choices import HistoryType
from taiga.projects.models import Project

from django.core.urlresolvers import reverse

pytestmark = pytest.mark.django_db

def test_project_totals_updated_on_activity(client):
    project = f.create_project()
    totals_updated_datetime = project.totals_updated_datetime
    now = datetime.datetime.now()
    assert project.total_activity == 0

    totals_updated_datetime = project.totals_updated_datetime
    us = f.UserStoryFactory.create(project=project, owner=project.owner)
    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": project.owner.id},
        comment="",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[],
        created_at=now - datetime.timedelta(days=3)
    )

    project = Project.objects.get(id=project.id)
    assert project.total_activity == 1
    assert project.total_activity_last_week == 1
    assert project.total_activity_last_month == 1
    assert project.total_activity_last_year == 1
    assert project.totals_updated_datetime > totals_updated_datetime

    totals_updated_datetime = project.totals_updated_datetime
    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": project.owner.id},
        comment="",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[],
        created_at=now - datetime.timedelta(days=13)
    )

    project = Project.objects.get(id=project.id)
    assert project.total_activity == 2
    assert project.total_activity_last_week == 1
    assert project.total_activity_last_month == 2
    assert project.total_activity_last_year == 2
    assert project.totals_updated_datetime > totals_updated_datetime

    totals_updated_datetime = project.totals_updated_datetime
    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": project.owner.id},
        comment="",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[],
        created_at=now - datetime.timedelta(days=33)
    )

    project = Project.objects.get(id=project.id)
    assert project.total_activity == 3
    assert project.total_activity_last_week == 1
    assert project.total_activity_last_month == 2
    assert project.total_activity_last_year == 3
    assert project.totals_updated_datetime > totals_updated_datetime

    totals_updated_datetime = project.totals_updated_datetime
    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": project.owner.id},
        comment="",
        type=HistoryType.change,
        key="userstories.userstory:{}".format(us.id),
        is_hidden=False,
        diff=[],
        created_at=now - datetime.timedelta(days=380)
    )

    project = Project.objects.get(id=project.id)
    assert project.total_activity == 4
    assert project.total_activity_last_week == 1
    assert project.total_activity_last_month == 2
    assert project.total_activity_last_year == 3
    assert project.totals_updated_datetime > totals_updated_datetime



def test_project_totals_updated_on_like(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)

    totals_updated_datetime = project.totals_updated_datetime
    now = datetime.datetime.now()
    assert project.total_activity == 0

    now = datetime.datetime.now()
    totals_updated_datetime = project.totals_updated_datetime
    us = f.UserStoryFactory.create(project=project, owner=project.owner)

    l = f.LikeFactory.create(content_object=project)
    l.created_date=now-datetime.timedelta(days=13)
    l.save()

    l = f.LikeFactory.create(content_object=project)
    l.created_date=now-datetime.timedelta(days=33)
    l.save()

    l = f.LikeFactory.create(content_object=project)
    l.created_date=now-datetime.timedelta(days=633)
    l.save()

    project.refresh_totals()
    project = Project.objects.get(id=project.id)

    assert project.total_fans == 3
    assert project.total_fans_last_week == 0
    assert project.total_fans_last_month == 1
    assert project.total_fans_last_year == 2
    assert project.totals_updated_datetime > totals_updated_datetime

    client.login(project.owner)
    url_like = reverse("projects-like", args=(project.id,))
    response = client.post(url_like)

    project = Project.objects.get(id=project.id)
    assert project.total_fans == 4
    assert project.total_fans_last_week == 1
    assert project.total_fans_last_month == 2
    assert project.total_fans_last_year == 3
    assert project.totals_updated_datetime > totals_updated_datetime
