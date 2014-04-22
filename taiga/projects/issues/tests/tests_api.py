# -*- coding: utf-8 -*-

import json

from django import test
from django.core import mail
from django.core.urlresolvers import reverse

from taiga.users.tests import create_user
from taiga.projects.tests import create_project, add_membership
from taiga.projects.milestones.tests import create_milestone
from taiga.projects.issues.models import Issue

from . import create_issue


class IssuesTestCase(test.TestCase):
    fixtures = ["initial_domains.json"]

    def setUp(self):
        self.user1 = create_user(1) # Project owner
        self.user2 = create_user(2) # Owner
        self.user3 = create_user(3) # Membership
        self.user4 = create_user(4) # No Membership

        self.project1 = create_project(1, self.user1)
        add_membership(self.project1, self.user2)
        add_membership(self.project1, self.user3)
        self.milestone1 = create_milestone(1, self.user2, self.project1)
        self.issue1 = create_issue(1, self.user2, self.project1, self.milestone1)
        self.issue2 = create_issue(2, self.user2, self.project1, self.milestone1)
        self.issue3 = create_issue(3, self.user2, self.project1)

        self.project2 = create_project(2, self.user4)
        self.milestone2 = create_milestone(2, self.user4, self.project2)
        self.issue4 = create_issue(4, self.user4, self.project2)

    def test_list_issues_by_anon(self):
        response = self.client.get(reverse("issues-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_issues_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-list"))
        self.assertEqual(response.status_code, 200)
        issues_list = response.data
        self.assertEqual(len(issues_list), 3)
        self.client.logout()

    def test_list_issues_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-list"))
        self.assertEqual(response.status_code, 200)
        issues_list = response.data
        self.assertEqual(len(issues_list), 3)
        self.client.logout()

    def test_list_issues_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-list"))
        self.assertEqual(response.status_code, 200)
        issues_list = response.data
        self.assertEqual(len(issues_list), 3)
        self.client.logout()

    def test_list_issues_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-list"))
        self.assertEqual(response.status_code, 200)
        issues_list = response.data
        self.assertEqual(len(issues_list), 1)
        self.client.logout()

    def test_view_issue_by_anon(self):
        response = self.client.get(reverse("issues-detail", args=(self.issue1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_issue_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-detail", args=(self.issue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_issue_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-detail", args=(self.issue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_issue_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-detail", args=(self.issue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_issue_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("issues-detail", args=(self.issue1.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_create_issue_by_anon(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Issue.objects.all().count(), 4)

    def test_create_issue_by_project_owner(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Issue.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 2)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_project(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project2.id,
            "status": self.project2.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_milestone(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_status(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project2.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_severity(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project2.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_priority(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project2.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_project_owner_with_wron_type(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project2.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Issue.objects.all().count(), 5)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_project(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project2.id,
            "status": self.project2.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_milestone(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone2.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_status(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project2.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_severity(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project2.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_priority(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project2.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_create_issue_by_membership_with_wron_type(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project2.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()


    def test_create_issue_by_no_membership(self):
        data = {
            "subject": "Test Issue",
            "description": "A Test Issue example description",
            "project": self.project1.id,
            "milestone": self.milestone1.id,
            "status": self.project1.issue_statuses.all()[1].id,
            "severity": self.project1.severities.all()[1].id,
            "priority": self.project1.priorities.all()[1].id,
            "type": self.project1.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("issues-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_anon(self):
        data = {
            "subject": "Edited test issue",
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.issue1.subject)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Issue.objects.all().count(), 4)

    def test_edit_issue_by_project_owner(self):
        data = {
            "subject": "Modified issue subject",
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.issue1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 2)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_status(self):
        data = {
            "status": self.project2.issue_statuses.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_severity(self):
        data = {
            "severity": self.project2.severities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_priority(self):
        data = {
            "priority": self.project2.priorities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_project_owner_with_wron_type(self):
        data = {
            "type": self.project2.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner(self):
        data = {
            "subject": "Modified issue subject",
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.issue1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_status(self):
        data = {
            "status": self.project2.issue_statuses.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_severity(self):
        data = {
            "severity": self.project2.severities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_priority(self):
        data = {
            "priority": self.project2.priorities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_owner_with_wron_type(self):
        data = {
            "type": self.project2.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership(self):
        data = {
            "subject": "Modified issue subject",
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.issue1.subject)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["subject"], response.data["subject"])
        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)

        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_milestone(self):
        data = {
            "milestone": self.milestone2.id,
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_status(self):
        data = {
            "status": self.project2.issue_statuses.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_severity(self):
        data = {
            "severity": self.project2.severities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_priority(self):
        data = {
            "priority": self.project2.priorities.all()[1].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_membership_with_wron_type(self):
        data = {
            "type": self.project2.issue_types.all()[0].id
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_edit_issue_by_no_membership(self):
        data = {
            "subject": "Modified issue subject",
        }

        self.assertEqual(Issue.objects.all().count(), 4)
        self.assertNotEqual(data["subject"], self.issue1.subject)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("issues-detail", args=(self.issue1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()

    def test_delete_issue_by_ano(self):
        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.delete(
                reverse("issues-detail", args=(self.issue1.id,))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Issue.objects.all().count(), 4)

    def test_delete_issue_by_project_owner(self):
        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("issues-detail", args=(self.issue1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Issue.objects.all().count(), 3)
        self.client.logout()

    def test_delete_issue_by_owner(self):
        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("issues-detail", args=(self.issue1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Issue.objects.all().count(), 3)
        self.client.logout()

    def test_delete_issue_by_membership(self):
        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("issues-detail", args=(self.issue1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Issue.objects.all().count(), 3)
        self.client.logout()

    def test_delete_issue_by_no_membership(self):
        self.assertEqual(Issue.objects.all().count(), 4)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("issues-detail", args=(self.issue1.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Issue.objects.all().count(), 4)
        self.client.logout()
