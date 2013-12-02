# -*- coding: utf-8 -*-

import uuid
import json

from django.core.urlresolvers import reverse
from django.conf.urls import patterns, include, url
from django import test
from django.db.models import get_model

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from greenmine import urls
from greenmine.base import auth
from greenmine.base.users.tests import create_user, create_site
from greenmine.projects.tests import create_project

from greenmine.base.models import Site, SiteMember
from greenmine.projects.models import Membership


class TestAuthView(viewsets.ViewSet):
    authentication_classes = (auth.Token,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response("ok")


urls.urlpatterns += patterns("",
    url(r'^test-api/v1/auth/', TestAuthView.as_view({"get": "get"}), name="test-token-auth"),
)


class TokenAuthTests(test.TestCase):
    fixtures = ["initial_site.json"]
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


class RegisterTests(test.TestCase):
    def setUp(self):
        self.user1 = create_user(1)
        self.site1 = create_site("localhost1", True)
        self.site2 = create_site("localhost2", False)
        self.role = self._create_role()
        self.project = create_project(1, self.user1)

    def test_public_register_01(self):
        data = {
            "username": "pepe",
            "password": "pepepepe",
            "first_name": "pepe",
            "last_name": "pepe",
            "email": "pepe@pepe.com",
            "type": "public",
        }

        url = reverse("auth-register")
        response = self.client.post(url, data, HTTP_X_HOST=self.site1.name)
        self.assertEqual(response.status_code, 201)

        self.assertEqual(SiteMember.objects.filter(site=self.site1).count(), 1)
        self.assertEqual(self.project.memberships.count(), 0)


    def test_public_register_02(self):
        data = {
            "username": "pepe",
            "password": "pepepepe",
            "first_name": "pepe",
            "last_name": "pepe",
            "email": "pepe@pepe.com",
            "type": "public",
        }

        url = reverse("auth-register")
        response = self.client.post(url, data, HTTP_X_HOST=self.site2.name)
        self.assertEqual(response.status_code, 400)

    def test_private_register_01(self):
        data = {
            "username": "pepe",
            "password": "pepepepe",
            "first_name": "pepe",
            "last_name": "pepe",
            "email": "pepe@pepe.com",
            "type": "private",
        }

        url = reverse("auth-register")
        response = self.client.post(url, data, HTTP_X_HOST=self.site2.name)
        self.assertEqual(response.status_code, 400)

    def test_private_register_02(self):
        membership = self._create_invitation("pepe@pepe.com")

        data = {
            "username": "pepe",
            "password": "pepepepe",
            "first_name": "pepe",
            "last_name": "pepe",
            "email": "pepe@pepe.com",
            "type": "private",
            "existing": False,
            "token": membership.token,
        }

        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 0)

        url = reverse("auth-register")
        response = self.client.post(url, data=json.dumps(data),
                                    content_type="application/json",
                                    HTTP_X_HOST=self.site2.name)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 1)
        self.assertEqual(self.project.memberships.get().role, self.role)
        self.assertEqual(SiteMember.objects.filter(site=self.site1).count(), 0)
        self.assertEqual(SiteMember.objects.filter(site=self.site2).count(), 1)

    def test_private_register_03(self):
        membership = self._create_invitation("pepe@pepe.com")

        data = {
            "username": self.user1.username,
            "password": self.user1.username,
            "type": "private",
            "existing": True,
            "token": membership.token,
        }

        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 0)

        url = reverse("auth-register")
        response = self.client.post(url, data=json.dumps(data),
                                    content_type="application/json",
                                    HTTP_X_HOST=self.site2.name)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 1)
        self.assertEqual(self.project.memberships.get().role, self.role)
        self.assertEqual(SiteMember.objects.filter(site=self.site1).count(), 0)
        self.assertEqual(SiteMember.objects.filter(site=self.site2).count(), 1)


    def _create_invitation(self, email):
        token = str(uuid.uuid1())
        membership_model = get_model("projects", "Membership")

        instance = membership_model(project=self.project,
                                    email=email,
                                    role=self.role,
                                    user=None,
                                    token=token)
        instance.save()
        return instance

    def _create_role(self):
        role_model = get_model("users", "Role")
        instance = role_model(name="foo", slug="foo",
                              order=1, computable=True)

        instance.save()
        return instance
