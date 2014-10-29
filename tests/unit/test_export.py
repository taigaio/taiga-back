# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from .. import factories as f

from taiga.export_import.service import project_to_dict

pytestmark = pytest.mark.django_db


def test_export_issue_finish_date(client):
    issue = f.IssueFactory.create(finished_date="2014-10-22")
    finish_date = project_to_dict(issue.project)["issues"][0]["finished_date"]
    assert finish_date == "2014-10-22T00:00:00+0000"


def test_export_user_story_finish_date(client):
    user_story = f.UserStoryFactory.create(finish_date="2014-10-22")
    finish_date = project_to_dict(user_story.project)["user_stories"][0]["finish_date"]
    assert finish_date == "2014-10-22T00:00:00+0000"
