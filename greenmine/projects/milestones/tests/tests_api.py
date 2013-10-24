# -*- coding: utf-8 -*-

import json

from django import test
from django.core import mail
from django.core.urlresolvers import reverse

from greenmine.base.users.tests import create_user
from greenmine.projects.tests import create_project, add_membership
from greenmine.projects.milestones.models import Milestone

from . import create_milestone


class MilestonesTestCase(test.TestCase):
    fixtures = ["initial_role.json", ]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user4 = create_user(4)

        self.project1 = create_project(1, self.user1)
        add_membership(self.project1, self.user2)
        add_membership(self.project1, self.user3)

        self.project2 = create_project(2, self.user4)

        self.milestone1 = create_milestone(1, self.user2, self.project1)
        self.milestone2 = create_milestone(2, self.user2, self.project1)

    def test_list_milestones_by_anon(self):
        response = self.client.get(reverse("milestones-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_milestones_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-list"))
        self.assertEqual(response.status_code, 200)
        milestones_list = response.data
        self.assertEqual(len(milestones_list), 2)
        self.client.logout()


    def test_list_milestones_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-list"))
        self.assertEqual(response.status_code, 200)
        milestones_list = response.data
        self.assertEqual(len(milestones_list), 2)
        self.client.logout()

    def test_list_milestones_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-list"))
        self.assertEqual(response.status_code, 200)
        milestones_list = response.data
        self.assertEqual(len(milestones_list), 2)
        self.client.logout()

    def test_list_milestones_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-list"))
        self.assertEqual(response.status_code, 200)
        milestones_list = response.data
        self.assertEqual(len(milestones_list), 0)
        self.client.logout()

    def test_view_milestone_by_anon(self):
        response = self.client.get(reverse("milestones-detail", args=(self.milestone1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_milestone_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-detail", args=(self.milestone1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_milestone_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-detail", args=(self.milestone1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_milestone_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-detail", args=(self.milestone1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_milestone_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("milestones-detail", args=(self.milestone1.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()


    def test_create_milestone_by_anon(self):
        data = {
            "name": "Test Milestone",
            "project": self.project1.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.post(
            reverse("milestones-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Milestone.objects.all().count(), 2)

    def test_create_milestone_by_project_owner(self):
        data = {
            "name": "Test Milestone",
            "project": self.project1.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("milestones-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Milestone.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_create_milestone_by_membership(self):
        data = {
            "name": "Test Milestone",
            "project": self.project1.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("milestones-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Milestone.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_create_milestone_by_membership_with_wron_project(self):
        data = {
            "name": "Test Milestone",
            "project": self.project2.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("milestones-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_create_milestone_by_no_membership(self):
        data = {
            "name": "Test Milestone",
            "project": self.project1.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("milestones-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_edit_milestone_by_anon(self):
        data = {
            "name": "Edited test milestone",
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertNotEqual(data["name"], self.milestone1.name)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Milestone.objects.all().count(), 2)

    def test_edit_milestone_by_project_owner(self):
        data = {
            "name": "Modified milestone name",
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertNotEqual(data["name"], self.milestone1.name)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], response.data["name"])
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_milestone_by_project_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_edit_milestone_by_owner(self):
        data = {
            "name": "Modified milestone name",
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertNotEqual(data["name"], self.milestone1.name)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], response.data["name"])
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_milestone_by_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_edit_milestone_by_membership(self):
        data = {
            "name": "Modified milestone name",
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertNotEqual(data["name"], self.milestone1.name)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], response.data["name"])
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 2)
        self.client.logout()

    def test_edit_milestone_by_membership_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_edit_milestone_by_no_membership(self):
        data = {
            "name": "Modified milestone name",
        }

        self.assertEqual(Milestone.objects.all().count(), 2)
        self.assertNotEqual(data["name"], self.milestone1.name)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("milestones-detail", args=(self.milestone1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

    def test_delete_milestone_by_ano(self):
        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.delete(
                reverse("milestones-detail", args=(self.milestone1.id,))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Milestone.objects.all().count(), 2)

    def test_delete_milestone_by_project_owner(self):
        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("milestones-detail", args=(self.milestone1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Milestone.objects.all().count(), 1)
        self.client.logout()

    def test_delete_milestone_by_owner(self):
        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("milestones-detail", args=(self.milestone1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Milestone.objects.all().count(), 1)
        self.client.logout()

    def test_delete_milestone_by_membership(self):
        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("milestones-detail", args=(self.milestone1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Milestone.objects.all().count(), 1)
        self.client.logout()

    def test_delete_milestone_by_no_membership(self):
        self.assertEqual(Milestone.objects.all().count(), 2)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("milestones-detail", args=(self.milestone1.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Milestone.objects.all().count(), 2)
        self.client.logout()

