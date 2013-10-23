# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.conf.urls import patterns, include, url
from django import test

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from greenmine import urls
from greenmine.base import auth
from greenmine.base.users.tests import create_user


class TestAuthView(APIView):
    authentication_classes = (auth.Token,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response("ok")


urls.urlpatterns += patterns("",
    url(r'^test-api/v1/auth/', TestAuthView.as_view(), name="test-token-auth"),
)


class SimpleTokenAuthTests(test.TestCase):
    def setUp(self):
        self.user1 = create_user(1)

    def test_token_auth_01(self):
        response = self.client.get(reverse("test-token-auth"))
        self.assertEqual(response.status_code, 401)

    def test_token_auth_02(self):
        token = auth.get_token_for_user(self.user1)
        response = self.client.get(reverse("test-token-auth"),
                                    HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"ok"')

