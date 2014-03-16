
from django import test
from django.test.client import RequestFactory
from django.http import HttpResponse

from . import middleware as mw


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
