# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
import io

from taiga.base.utils import json
from taiga.export_import.services import render_project

from tests.utils import disconnect_signals, reconnect_signals

from .. import factories as f


pytestmark = pytest.mark.django_db(transaction=True)


def setup_module():
    disconnect_signals()


def teardown_module():
    reconnect_signals()


def test_export_issue_finish_date(client):
    issue = f.IssueFactory.create(finished_date="2014-10-22T00:00:00+0000")
    output = io.BytesIO()
    render_project(issue.project, output)
    project_data = json.loads(output.getvalue())
    finish_date = project_data["issues"][0]["finished_date"]
    assert finish_date == "2014-10-22T00:00:00+0000"


def test_export_user_story_finish_date(client):
    user_story = f.UserStoryFactory.create(finish_date="2014-10-22T00:00:00+0000")
    output = io.BytesIO()
    render_project(user_story.project, output)
    project_data = json.loads(output.getvalue())
    finish_date = project_data["user_stories"][0]["finish_date"]
    assert finish_date == "2014-10-22T00:00:00+0000"


def test_export_epic_with_user_stories(client):
    epic = f.EpicFactory.create(subject="test epic export")
    user_story = f.UserStoryFactory.create(project=epic.project)
    f.RelatedUserStory.create(epic=epic, user_story=user_story)
    output = io.BytesIO()
    render_project(user_story.project, output)
    project_data = json.loads(output.getvalue())
    assert project_data["epics"][0]["subject"] == "test epic export"
    assert len(project_data["epics"]) == 1

    assert project_data["epics"][0]["related_user_stories"][0]["user_story"] == user_story.ref
    assert len(project_data["epics"][0]["related_user_stories"]) == 1
