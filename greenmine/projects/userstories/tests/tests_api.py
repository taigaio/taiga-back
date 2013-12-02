# -*- coding: utf-8 -*-

import json

from django import test
from django.core import mail
from django.core.urlresolvers import reverse

from greenmine.base.users.tests import create_user
from greenmine.projects.tests import create_project, add_membership
from greenmine.projects.milestones.tests import create_milestone
from greenmine.projects.userstories.models import UserStory

from . import create_userstory


class UserStoriesTestCase(test.TestCase):
    fixtures = ["initial_role.json", "initial_site.json"]

    def setUp(self):
        self.user1 = create_user(1) # Project owner
        self.user2 = create_user(2) # Owner
        self.user3 = create_user(3) # Membership
        self.user4 = create_user(4) # No Membership

        self.project1 = create_project(1, self.user1)
        add_membership(self.project1, self.user2)
        add_membership(self.project1, self.user3)
        self.milestone1 = create_milestone(1, self.user2, self.project1)
        self.userstory1 = create_userstory(1, self.user2, self.project1, self.milestone1)
        self.userstory2 = create_userstory(2, self.user2, self.project1, self.milestone1)
        self.userstory3 = create_userstory(3, self.user2, self.project1)

        self.project2 = create_project(2, self.user4)
        self.milestone2 = create_milestone(2, self.user4, self.project2)
        self.userstory4 = create_userstory(4, self.user4, self.project2)

    def test_list_userstories_by_anon(self):
        response = self.client.get(reverse("userstories-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_userstories_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-list"))
        self.assertEqual(response.status_code, 200)
        userstories_list = response.data
        self.assertEqual(len(userstories_list), 3)
        self.client.logout()

    def test_list_userstories_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-list"))
        self.assertEqual(response.status_code, 200)
        userstories_list = response.data
        self.assertEqual(len(userstories_list), 3)
        self.client.logout()

    def test_list_userstories_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-list"))
        self.assertEqual(response.status_code, 200)
        userstories_list = response.data
        self.assertEqual(len(userstories_list), 3)
        self.client.logout()

    def test_list_userstories_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-list"))
        self.assertEqual(response.status_code, 200)
        userstories_list = response.data
        self.assertEqual(len(userstories_list), 1)
        self.client.logout()

    def test_view_userstory_by_anon(self):
        response = self.client.get(reverse("userstories-detail", args=(self.userstory1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_userstory_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-detail", args=(self.userstory1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_userstory_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-detail", args=(self.userstory1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_userstory_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-detail", args=(self.userstory1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_userstory_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("userstories-detail", args=(self.userstory1.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_create_userstory_by_anon(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(UserStory.objects.all().count(), 4)

    def test_create_userstory_by_project_owner(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserStory.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_create_userstory_by_project_owner_with_wron_project(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project2.id,
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_project_owner_with_wron_milestone(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_project_owner_with_wron_status(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_membership(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserStory.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_create_userstory_by_membership_with_wron_project(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project2.id,
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_membership_with_wron_milestone(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_membership_with_wron_status(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_create_userstory_by_no_membership(self):
        data = {
            "subject": "Test UserStory",
            "description": "A Test UserStory example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("userstories-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_anon(self):
        data = {
            "subject": "Edited test userstory",
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.userstory1.subject)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(UserStory.objects.all().count(), 4)

    def test_edit_userstory_by_project_owner(self):
        data = {
            "subject": "Modified userstory subject",
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.userstory1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_userstory_by_project_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_project_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_project_owner_with_wron_status(self):
        data = {
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_owner(self):
        data = {
            "subject": "Modified userstory subject",
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.userstory1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_userstory_by_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_owner_with_wron_status(self):
        data = {
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_membership(self):
        data = {
            "subject": "Modified userstory subject",
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.userstory1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 2)
        self.client.logout()

    def test_edit_userstory_by_membership_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_membership_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_membership_with_wron_status(self):
        data = {
            "status": self.project2.us_statuses.all()[1].id
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_edit_userstory_by_no_membership(self):
        data = {
            "subject": "Modified userstory subject",
        }

        self.assertEqual(UserStory.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.userstory1.subject)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("userstories-detail", args=(self.userstory1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()

    def test_delete_userstory_by_ano(self):
        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.delete(
                reverse("userstories-detail", args=(self.userstory1.id,))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(UserStory.objects.all().count(), 4)

    def test_delete_userstory_by_project_owner(self):
        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("userstories-detail", args=(self.userstory1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserStory.objects.all().count(), 3)
        self.client.logout()

    def test_delete_userstory_by_owner(self):
        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("userstories-detail", args=(self.userstory1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserStory.objects.all().count(), 3)
        self.client.logout()

    def test_delete_userstory_by_membership(self):
        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("userstories-detail", args=(self.userstory1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserStory.objects.all().count(), 3)
        self.client.logout()

    def test_delete_userstory_by_no_membership(self):
        self.assertEqual(UserStory.objects.all().count(), 4)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("userstories-detail", args=(self.userstory1.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(UserStory.objects.all().count(), 4)
        self.client.logout()
