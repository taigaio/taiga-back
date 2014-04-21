# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from django import test
from django.test.client import RequestFactory
from django.http import HttpResponse

from taiga.projects.tests import create_project
from taiga.projects.issues.tests import create_issue
from taiga.base.users.tests import create_user

from . import middleware as mw
from . import changes as ch


class SessionIDMiddlewareTests(test.TestCase):
    # fixtures = ["initial_domains.json"]

    def setUp(self):
        self.factory = RequestFactory()

    def test_process_session_id_01(self):
        request = self.factory.get("/")

        mw_instance = mw.SessionIDMiddleware()
        mw_instance.process_request(request)

        self.assertEqual(mw.get_current_session_id(), None)

    def test_process_session_id_02(self):
        request = self.factory.get("/", HTTP_X_SESSION_ID="foobar")

        mw_instance = mw.SessionIDMiddleware()
        mw_instance.process_request(request)

        self.assertEqual(mw.get_current_session_id(), "foobar")


from unittest.mock import MagicMock
from unittest.mock import patch

class ChangesTest(test.TestCase):
    fixtures = ["initial_domains.json"]

    def test_emit_change_for_model(self):
        user = create_user(1) # Project owner
        project = create_project(1, user)
        issue = create_issue(1, user, project)

        with patch("taiga.events.backends.get_events_backend") as mock_instance:
            ch.emit_change_event_for_model(issue, "sessionid")
            self.assertTrue(mock_instance.return_value.emit_event.called)
