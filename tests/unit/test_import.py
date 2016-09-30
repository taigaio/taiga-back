# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
import io
from .. import factories as f

from taiga.base.utils import json
from taiga.export_import.services import render_project, store_project_from_dict

pytestmark = pytest.mark.django_db


def test_import_epic_with_user_stories(client):
    project = f.ProjectFactory()
    project.default_points = f.PointsFactory.create(project=project)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_epic_status = f.EpicStatusFactory.create(project=project)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)

    epic = f.EpicFactory.create(subject="test epic export", project=project, status=project.default_epic_status)
    user_story = f.UserStoryFactory.create(project=project, status=project.default_us_status, milestone=None)
    f.RelatedUserStory.create(epic=epic, user_story=user_story, order=55)
    output = io.BytesIO()
    render_project(user_story.project, output)
    project_data = json.loads(output.getvalue())

    epic.project.delete()

    project = store_project_from_dict(project_data)
    assert project.epics.count() == 1
    assert project.epics.first().ref == epic.ref

    assert project.epics.first().user_stories.count() == 1
    related_userstory = project.epics.first().relateduserstory_set.first()
    assert related_userstory.user_story.ref == user_story.ref
    assert related_userstory.order == 55
    assert related_userstory.epic.ref == epic.ref
