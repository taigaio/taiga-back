# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

import datetime

from .. import factories as f

from taiga.projects.history.choices import HistoryType
from taiga.projects.models import Project

from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_project_totals_updated_on_activity(client):
    project = f.create_project()
    totals_updated_datetime = project.totals_updated_datetime
    now = timezone.now()
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
    now = timezone.now()
    assert project.total_activity == 0

    now = timezone.now()
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
