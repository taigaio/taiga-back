# -*- coding: utf-8 -*-

import uuid
import json

from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django import test
from django.db.models import get_model

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from taiga import urls
from taiga.base import exceptions as exc
from taiga.users.tests import create_user, create_domain
from taiga.domains.models import DomainMember
from taiga.domains.services import is_user_exists_on_domain
from taiga.domains import get_default_domain
from taiga.auth.backends import Token as TokenAuthBackend
from taiga.auth.backends import get_token_for_user
from taiga.auth import services

from taiga.projects.tests import create_project
from taiga.projects.tests import add_membership


class TestAuthView(viewsets.ViewSet):
    authentication_classes = (TokenAuthBackend,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response("ok")


urls.urlpatterns += patterns("",
    url(r'^test-api/v1/auth/', TestAuthView.as_view({"get": "get"}), name="test-token-auth"),
)


class AuthServicesTests(test.TestCase):
    fixtures = ["initial_domains.json",]

    def setUp(self):
        self.user1 = create_user(1)
        self.domain = get_default_domain()

    def test_send_public_register_email(self):
        """
        This test should explictly fail because these emails
        at this momment does not exists.
        """

        with self.assertRaises(Exception):
            services.send_public_register_email(self.user1)

    def test_send_private_register_email(self):
        """
        This test should explictly fail because these emails
        at this momment does not exists.
        """

        with self.assertRaises(Exception):
            services.send_private_register_email(self.user1)

    def test_is_user_already_registred(self):
        username = self.user1.username
        email = self.user1.email

        self.assertTrue(services.is_user_already_registred(username=username, email=email))
        self.assertTrue(services.is_user_already_registred(username=username, email="foo@bar.com"))
        self.assertTrue(services.is_user_already_registred(username="foo", email=email))
        self.assertFalse(services.is_user_already_registred(username="foo", email="foo@bar.com"))

    def test_get_membership_by_token(self):
        with self.assertRaises(exc.NotFound):
            services.get_membership_by_token("invalidtoken")

        project = create_project(1, self.user1)
        membership = add_membership(project, self.user1, "back")
        membership.token = "foobar"
        membership.save()

        m = services.get_membership_by_token("foobar")
        self.assertEqual(m.id, membership.id)

    def test_public_register(self):
        with self.assertRaises(exc.IntegrityError):
            services.public_register(self.domain,
                                     username=self.user1.username,
                                     password="secret",
                                     email=self.user1.email,
                                     first_name="foo",
                                     last_name="bar")

        user = services.public_register(self.domain,
                                        username="foousername",
                                        password="foosecret",
                                        email="foo@bar.ca",
                                        first_name="Foo",
                                        last_name="Bar")
        self.assertEqual(user.username, "foousername")
        self.assertTrue(user.check_password("foosecret"))
        self.assertTrue(is_user_exists_on_domain(self.domain, user))

    def test_private_register(self):
        project = create_project(1, self.user1)

        membership = add_membership(project, self.user1, "back")
        membership.user = None
        membership.token = "foobar"
        membership.save()

        # Try register with invalid token
        with self.assertRaises(exc.NotFound):
            services.private_register_for_existing_user(self.domain,
                                                        token="barfoo",
                                                        username=self.user1.username,
                                                        password=self.user1.username)

        # Try register with valid token and valid existing user
        self.assertEqual(membership.user, None)
        user = services.private_register_for_existing_user(self.domain,
                                                           token="foobar",
                                                           username=self.user1.username,
                                                           password=self.user1.username)

        membership = membership.__class__.objects.get(pk=membership.pk)
        self.assertEqual(membership.user, user)

        # Try register new user
        membership.user = None
        membership.token = "token"
        membership.save()

        user = services.private_register_for_new_user(self.domain,
                                                      token="token",
                                                      username="user2",
                                                      password="user2",
                                                      email="user2@bar.ca",
                                                      first_name="Foo",
                                                      last_name="Bar")


        membership = membership.__class__.objects.get(pk=membership.pk)
        self.assertEqual(membership.user, user)
        self.assertTrue(is_user_exists_on_domain(self.domain, user))



class TokenAuthenticationBackendTests(test.TestCase):
    fixtures = ["initial_domains.json",]

    def setUp(self):
        self.user1 = create_user(1)

    def test_token_auth_01(self):
        response = self.client.get(reverse("test-token-auth"))
        self.assertEqual(response.status_code, 401)

    def test_token_auth_02(self):
        token = get_token_for_user(self.user1)
        response = self.client.get(reverse("test-token-auth"),
                                   HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"ok"')


class RegisterApiTests(test.TestCase):
    fixtures = ["initial_domains.json",]

    def setUp(self):
        self.user1 = create_user(1)
        self.domain1 = create_domain("localhost1", True)
        self.domain2 = create_domain("localhost2", False)
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
        response = self.client.post(url, data, HTTP_X_HOST=self.domain1.name)
        self.assertEqual(response.status_code, 201)

        self.assertEqual(DomainMember.objects.filter(domain=self.domain1).count(), 1)
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
        response = self.client.post(url, data, HTTP_X_HOST=self.domain2.name)
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
        response = self.client.post(url, data, HTTP_X_HOST=self.domain2.name)
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
                                    HTTP_X_HOST=self.domain2.name)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 1)
        self.assertEqual(self.project.memberships.get().role, self.role)
        self.assertEqual(DomainMember.objects.filter(domain=self.domain1).count(), 0)
        self.assertEqual(DomainMember.objects.filter(domain=self.domain2).count(), 1)

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
                                    HTTP_X_HOST=self.domain2.name)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.memberships.exclude(user__isnull=True).count(), 1)
        self.assertEqual(self.project.memberships.get().role, self.role)
        self.assertEqual(DomainMember.objects.filter(domain=self.domain1).count(), 0)
        self.assertEqual(DomainMember.objects.filter(domain=self.domain2).count(), 1)

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
                              order=1, computable=True, project_id=1)

        instance.save()
        return instance
