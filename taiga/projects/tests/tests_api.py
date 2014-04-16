# -*- coding: utf-8 -*-

import json

from django import test
from django.core.urlresolvers import reverse
from django.core import mail
from django.db.models import get_model

from taiga.users.tests import create_user
from taiga.projects.models import Project, Membership

from . import create_project
from . import add_membership


class ProfileTestCase(test.TestCase):
    fixtures = ["initial_domains.json"]

    def setUp(self):
        self.user1 = create_user(1, is_superuser=True)
        self.user2 = create_user(2)
        self.user3 = create_user(3)

        self.project1 = create_project(1, self.user1)
        self.project2 = create_project(2, self.user1)
        self.project3 = create_project(3, self.user2)

        add_membership(self.project1, self.user3, "back")
        add_membership(self.project3, self.user3, "back")
        add_membership(self.project3, self.user2, "back")


    def test_list_users(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        response = self.client.get(reverse("users-list"))
        self.assertEqual(response.status_code, 200)

        users_list = response.data
        self.assertEqual(len(users_list), 1)

        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        response = self.client.get(reverse("users-list"))
        self.assertEqual(response.status_code, 200)

        users_list = response.data
        self.assertEqual(len(users_list), 3)


    def test_update_users(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}

        response = self.client.patch(
                        reverse("users-detail", args=[self.user2.pk]),
                        content_type="application/json",
                        data=json.dumps(data))
        self.assertEqual(response.status_code, 404)

    def test_update_users_self(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}
        response = self.client.patch(
                        reverse("users-detail", args=[self.user3.pk]),
                        content_type="application/json",
                        data=json.dumps(data))

        self.assertEqual(response.status_code, 200)

    def test_update_users_superuser(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}
        response = self.client.patch(
                        reverse("users-detail", args=[self.user3.pk]),
                        content_type="application/json",
                        data=json.dumps(data))

        self.assertEqual(response.status_code, 200)

    def test_delete_users(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}
        response = self.client.delete(
                        reverse("users-detail", args=[self.user2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_users_self(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}
        response = self.client.delete(
                        reverse("users-detail", args=[self.user3.pk]))

        self.assertEqual(response.status_code, 204)


    def test_delete_users_superuser(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        data = {"first_name": "Foo Bar"}
        response = self.client.delete(
                        reverse("users-detail", args=[self.user3.pk]))

        self.assertEqual(response.status_code, 204)

    def test_password_recovery(self):
        url = reverse("users-password-recovery")
        data = {"username": self.user1.username}

        response = self.client.post(url, data=json.dumps(data),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotEqual(len(mail.outbox[0].body), 0)

    def test_users_change_password_from_recovery(self):
        self.user1.token = "1111-1111-1111-1111"
        self.user1.save()

        url = reverse("users-change-password-from-recovery")
        data = {"token": self.user1.token, "password": "111111"}

        response = self.client.post(url, data=json.dumps(data),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 204)

        user = get_model("users", "User").objects.get(pk=self.user1.pk)
        self.assertTrue(user.check_password("111111"))

    def test_users_change_password(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        url = reverse("users-change-password")
        data = {"password": "111111"}

        response = self.client.post(url, data=json.dumps(data),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 204)

        user = get_model("users", "User").objects.get(pk=self.user1.pk)
        self.assertTrue(user.check_password("111111"))


class ProjectsTestCase(test.TestCase):
    fixtures = ["initial_role.json", "initial_domains.json"]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user3 = create_user(4)

        self.project1 = create_project(1, self.user1)
        self.project2 = create_project(2, self.user1)
        self.project3 = create_project(3, self.user2)
        self.project4 = create_project(4, self.user2)

        add_membership(self.project1, self.user3, "back")
        add_membership(self.project3, self.user3, "back")

        self.dev_role1 = get_model("users", "Role").objects.get(slug="back", project=self.project1)
        self.dev_role2 = get_model("users", "Role").objects.get(slug="back", project=self.project2)
        self.dev_role3 = get_model("users", "Role").objects.get(slug="back", project=self.project3)
        self.dev_role4 = get_model("users", "Role").objects.get(slug="back", project=self.project4)

    def test_send_invitations_01(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        url = reverse("memberships-list")
        data = {"role": self.dev_role4.id,
                "email": "pepe@pepe.com",
                "project": self.project4.id}

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project4.memberships.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotEqual(len(mail.outbox[0].body), 0)

    def test_send_invitations_02(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        url = reverse("memberships-list")
        data = {"role": self.dev_role4.id,
                "email": "pepe@pepe.com",
                "project": self.project4.id}

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project4.memberships.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotEqual(len(mail.outbox[0].body), 0)

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(self.project4.memberships.count(), 1)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotEqual(len(mail.outbox[0].body), 0)

    def test_send_invitations_03(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)

        url = reverse("memberships-list")
        data = {"role": self.dev_role3.id,
                "email": self.user3.email,
                "project": self.project3.id}

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(len(mail.outbox), 0)

    def test_list_projects_by_anon(self):
        response = self.client.get(reverse("projects-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_projects_by_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-list"))
        self.assertEqual(response.status_code, 200)
        projects_list = response.data
        self.assertEqual(len(projects_list), 2)
        self.client.logout()

        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-list"))
        self.assertEqual(response.status_code, 200)
        projects_list = response.data
        self.assertEqual(len(projects_list), 2)
        self.client.logout()

    def test_list_projects_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-list"))
        self.assertEqual(response.status_code, 200)
        projects_list = response.data
        self.assertEqual(len(projects_list), 2)
        self.client.logout()

    def test_view_project_by_anon(self):
        response = self.client.get(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_project_by_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("projects-detail", args=(self.project2.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_project_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("projects-detail", args=(self.project3.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_project_by_not_membership(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("projects-detail", args=(self.project3.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_create_project_by_anon(self):
        data = {
            "name": "Test Project",
            "description": "A new Test Project",
            "total_story_points": 10
        }

        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.post(
            reverse("projects-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Project.objects.all().count(), 4)

    def test_create_project_by_auth(self):
        data = {
            "name": "Test Project",
            "description": "A new Test Project",
            "total_story_points": 10
        }

        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(reverse("projects-list"), json.dumps(data),
                                    content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.all().count(), 5)
        self.client.logout()

    def test_edit_project_by_anon(self):
        data = {
            "description": "Edited project description",
        }

        self.assertEqual(Project.objects.all().count(), 4)
        self.assertNotEqual(data["description"], self.project1.description)
        response = self.client.patch(
            reverse("projects-detail", args=(self.project1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Project.objects.all().count(), 4)

    def test_edit_project_by_owner(self):
        data = {
            "description": "Modified project description",
        }

        self.assertEqual(Project.objects.all().count(), 4)
        self.assertNotEqual(data["description"], self.project1.description)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("projects-detail", args=(self.project1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["description"], response.data["description"])
        self.assertEqual(Project.objects.all().count(), 4)
        self.client.logout()

    def test_edit_project_by_membership(self):
        data = {
            "description": "Edited project description",
        }

        self.assertEqual(Project.objects.all().count(), 4)
        self.assertNotEqual(data["description"], self.project1.description)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("projects-detail", args=(self.project1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["description"], response.data["description"])
        self.assertEqual(Project.objects.all().count(), 4)
        self.client.logout()

    def test_edit_project_by_not_membership(self):
        data = {
            "description": "Edited project description",
        }

        self.assertEqual(Project.objects.all().count(), 4)
        self.assertNotEqual(data["description"], self.project1.description)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("projects-detail", args=(self.project1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Project.objects.all().count(), 4)
        self.client.logout()

    def test_delete_project_by_anon(self):
        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.delete(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Project.objects.all().count(), 4)

    def test_delete_project_by_owner(self):
        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Project.objects.all().count(), 3)
        self.client.logout()

    def test_delete_project_by_membership(self):
        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(reverse("projects-detail", args=(self.project1.id,)))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Project.objects.all().count(), 4)
        self.client.logout()

    def test_delete_project_by_not_membership(self):
        self.assertEqual(Project.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(reverse("projects-detail", args=(self.project3.id,)))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Project.objects.all().count(), 4)
        self.client.logout()
