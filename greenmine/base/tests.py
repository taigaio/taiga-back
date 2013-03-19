# -*- coding: utf-8 -*-

from django.conf import settings
from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from ..models import *

from django.utils import timezone
import datetime
import json

from greenqueue import send_task


class LowLevelEmailTests(TestCase):
    def setUp(self):
        mail.outbox = []

    def test_send_one_mail(self):
        send_task("send-mail", args = ["subject", "template", ["hola@niwi.be"]])
        self.assertEqual(len(mail.outbox), 1)

    def test_send_bulk_mail(self):
        send_task("send-bulk-mail", args = [[
            ('s1', 't1', ['hola@niwi.be']),
            ('s2', 't2', ['hola@niwi.be']),
        ]])

        self.assertEqual(len(mail.outbox), 2)


class UserMailTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username = 'test1',
            email = 'test1@test.com',
            is_active = True,
            is_staff = True,
            is_superuser = True,
        )

        self.user2 = User.objects.create(
            username = 'test2',
            email = 'test2@test.com',
            is_active = True,
            is_staff = False,
            is_superuser = False,
        )

        self.user1.set_password("test")
        self.user2.set_password("test")

        self.user1.save()
        self.user2.save()

        mail.outbox = []

    def test_remember_password(self):
        url = reverse("remember-password")

        post_params = {'email': 'test2@test.com'}
        response = self.client.post(url, post_params, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        jdata = json.loads(response.content)
        self.assertIn("valid", jdata)
        self.assertTrue(jdata['valid'])

    def test_remember_password_not_exists(self):
        url = reverse("remember-password")

        post_params = {'email': 'test2@testa.com'}
        response = self.client.post(url, post_params, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        jdata = json.loads(response.content)
        self.assertIn("valid", jdata)
        self.assertFalse(jdata['valid'])

    def test_send_recovery_password_by_staff(self):
        url = reverse("users-recovery-password", args=[self.user2.pk])

        ok = self.client.login(username="test1", password="test")
        self.assertTrue(ok)

        # pre test
        self.assertTrue(self.user2.is_active)
        self.assertEqual(self.user2.get_profile().token, None)

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

        # expected redirect
        self.assertEqual(response.redirect_chain, [('http://testserver/users/2/edit/', 302)])

        # test mail sending
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Greenmine: password recovery.")

        # test user model modification
        self.user2 = User.objects.get(pk=self.user2.pk)
        self.assertTrue(self.user2.is_active)
        self.assertFalse(self.user2.has_usable_password())
        self.assertNotEqual(self.user2.get_profile().token, None)

        url = reverse('password-recovery', args=[self.user2.get_profile().token])

        post_params = {
            'password': '123123',
            'password2': '123123',
        }
        response = self.client.post(url, post_params, follow=True)

        self.assertEqual(response.status_code, 200)

        # expected redirect
        self.assertEqual(response.redirect_chain, [('http://testserver/login/', 302)])

        ok = self.client.login(username="test2", password="123123")
        self.assertTrue(ok)

