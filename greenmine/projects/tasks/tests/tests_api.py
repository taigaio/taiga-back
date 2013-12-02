# -*- coding: utf-8 -*-

import json

from django import test
from django.core import mail
from django.core.urlresolvers import reverse

import reversion

from greenmine.base.users.tests import create_user
from greenmine.projects.tests import create_project, add_membership
from greenmine.projects.milestones.tests import create_milestone
from greenmine.projects.userstories.tests import create_userstory
from greenmine.projects.tasks.models import Task

from . import create_task


class TasksTestCase(test.TestCase):
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
        self.task1 = create_task(1, self.user2, self.project1, None, self.userstory1)
        self.task2 = create_task(2, self.user3, self.project1, None, self.userstory1)
        self.task3 = create_task(3, self.user2, self.project1, None, self.userstory2)
        self.task4 = create_task(4, self.user3, self.project1, self.milestone1)

        self.project2 = create_project(2, self.user4)
        self.milestone2 = create_milestone(2, self.user4, self.project2)
        self.userstory4 = create_userstory(4, self.user4, self.project2)
        self.task5 = create_task(5, self.user4, self.project2, self.milestone2)

    def test_list_tasks_by_anon(self):
        response = self.client.get(reverse("tasks-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_tasks_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-list"), HTTP_X_DISABLE_PAGINATION=True)
        self.assertEqual(response.status_code, 200)
        tasks_list = response.data
        self.assertEqual(len(tasks_list), 4)

        response = self.client.get(reverse("tasks-list"), {"page": 2},
                                   HTTP_X_DISABLE_PAGINATION=True)
        self.assertEqual(response.status_code, 200)
        tasks_list = response.data
        self.assertEqual(len(tasks_list), 4)
        self.client.logout()

    def test_list_tasks_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-list"))
        self.assertEqual(response.status_code, 200)
        tasks_list = response.data
        self.assertEqual(len(tasks_list), 4)
        self.client.logout()

    def test_list_tasks_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-list"))
        self.assertEqual(response.status_code, 200)
        tasks_list = response.data
        self.assertEqual(len(tasks_list), 4)
        self.client.logout()

    def test_list_tasks_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-list"))
        self.assertEqual(response.status_code, 200)
        tasks_list = response.data
        self.assertEqual(len(tasks_list), 1)
        self.client.logout()

    def test_view_task_by_anon(self):
        response = self.client.get(reverse("tasks-detail", args=(self.task1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_task_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        # Change task for generate history/diff.
        with reversion.create_revision():
            self.task1.tags = ["LL"]
            self.task1.save()

        with reversion.create_revision():
            self.task1.tags = ["LLKK"]
            self.task1.save()

        response = self.client.get(reverse("tasks-detail", args=(self.task1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_task_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-detail", args=(self.task1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_task_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-detail", args=(self.task1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_task_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("tasks-detail", args=(self.task1.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_create_task_by_anon(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Task.objects.all().count(), 5)

    def test_create_task_by_project_owner(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.all().count(), 6)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_create_task_by_project_owner_with_wron_project(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project2.id,
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_project_owner_with_wron_milestone(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_project_owner_with_wron_userstory(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "user_story": self.userstory4.id,
            "status": self.project1.task_statuses.all()[1].id,
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_project_owner_with_wron_status(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_membership(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.all().count(), 6)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_create_task_by_membership_with_wron_project(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project2.id,
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_membership_with_wron_milestone(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_membership_with_wron_userstory(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "user_story": self.userstory4.id,
            "status": self.project1.task_statuses.all()[1].id,
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_membership_with_wron_status(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_create_task_by_no_membership(self):
        data = {
            "subject": "Test Task",
            "description": "A Test Task example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("tasks-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_anon(self):
        data = {
            "subject": "Edited test task",
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertNotEqual(data["subject"], self.task1.subject)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Task.objects.all().count(), 5)

    def test_edit_task_by_project_owner(self):
        data = {
            "subject": "Modified task subject",
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertNotEqual(data["subject"], self.task1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_task_by_project_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_project_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["milestone"], self.milestone1.id)
        self.assertEqual(Task.objects.all().count(), 5)

        data = {
            "milestone": self.milestone2.id,
            "user_story": None
        }

        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_project_owner_with_wron_userstory(self):
        data = {
            "user_story": self.userstory4.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_project_owner_with_wron_status(self):
        data = {
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_owner(self):
        data = {
            "subject": "Modified task subject",
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertNotEqual(data["subject"], self.task1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_task_by_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["milestone"], self.milestone1.id)
        self.assertEqual(Task.objects.all().count(), 5)

        data = {
            "milestone": self.milestone2.id,
            "user_story": None
        }

        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_owner_with_wron_userstory(self):
        data = {
            "user_story": self.userstory4.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_owner_with_wron_status(self):
        data = {
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_membership(self):
        data = {
            "subject": "Modified task subject",
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertNotEqual(data["subject"], self.task1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Task.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 2)
        self.client.logout()

    def test_edit_task_by_membership_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_membership_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["milestone"], self.milestone1.id)
        self.assertEqual(Task.objects.all().count(), 5)

        data = {
            "milestone": self.milestone2.id,
            "user_story": None
        }

        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_membership_with_wron_userstory(self):
        data = {
            "user_story": self.userstory4.id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_membership_with_wron_status(self):
        data = {
            "status": self.project2.task_statuses.all()[1].id
        }

        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_edit_task_by_no_membership(self):
        data = {
            "subject": "Modified task subject",
        }

        self.assertEqual(Task.objects.all().count(), 5)
        self.assertNotEqual(data["subject"], self.task1.subject)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("tasks-detail", args=(self.task1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()

    def test_delete_task_by_ano(self):
        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.delete(
                reverse("tasks-detail", args=(self.task1.id,))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Task.objects.all().count(), 5)

    def test_delete_task_by_project_owner(self):
        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("tasks-detail", args=(self.task1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Task.objects.all().count(), 4)
        self.client.logout()

    def test_delete_task_by_owner(self):
        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("tasks-detail", args=(self.task1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Task.objects.all().count(), 4)
        self.client.logout()

    def test_delete_task_by_membership(self):
        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("tasks-detail", args=(self.task1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Task.objects.all().count(), 4)
        self.client.logout()

    def test_delete_task_by_no_membership(self):
        self.assertEqual(Task.objects.all().count(), 5)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("tasks-detail", args=(self.task1.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.all().count(), 5)
        self.client.logout()
