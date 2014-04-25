# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

from django import test
from django.core.urlresolvers import reverse
from django.core import mail
from django.db.models import get_model

from taiga.users.tests import create_user
from taiga.projects.models import Project, Membership
from taiga.projects.issues.tests import create_issue
from taiga.projects.tasks.tests import create_task

from . import create_project
from . import add_membership

class AllProjectEventsNotificationsTestCase(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user4 = create_user(4)
        self.user5 = create_user(5)

        self.user1.notify_level = "all_owned_projects"
        self.user1.save()
        self.user2.notify_level = "all_owned_projects"
        self.user2.save()
        self.user3.notify_level = "all_owned_projects"
        self.user3.save()
        self.user4.notify_level = "all_owned_projects"
        self.user4.save()
        self.user5.notify_level = "all_owned_projects"
        self.user5.save()

        self.project1 = create_project(1, self.user1)

        add_membership(self.project1, self.user1, "back")
        add_membership(self.project1, self.user2, "back")
        add_membership(self.project1, self.user3, "back")
        add_membership(self.project1, self.user4, "back")
        add_membership(self.project1, self.user5, "back")

    def test_issue(self):
        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user2, self.user3, self.user4, self.user5]

        self.assertEqual(notified,set(expected_notified))
        issue.delete()

    def test_issue_with_owner_notification(self):
        self.user1.notify_changes_by_me = True
        self.user1.save()

        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user1, self.user2, self.user3, self.user4, self.user5]

        self.assertEqual(notified,set(expected_notified))
        issue.delete()
        self.user1.notify_changes_by_me = False
        self.user1.save()

class OnlyAssigendNotificationsTestCase(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user4 = create_user(4)
        self.user5 = create_user(5)

        self.user1.notify_level = "only_assigned"
        self.user1.save()
        self.user2.notify_level = "only_assigned"
        self.user2.save()
        self.user3.notify_level = "only_assigned"
        self.user3.save()
        self.user4.notify_level = "only_assigned"
        self.user4.save()
        self.user5.notify_level = "only_assigned"
        self.user5.save()

        self.project1 = create_project(1, self.user1)

        add_membership(self.project1, self.user1, "back")
        add_membership(self.project1, self.user2, "back")
        add_membership(self.project1, self.user3, "back")
        add_membership(self.project1, self.user4, "back")
        add_membership(self.project1, self.user5, "back")

    def test_issue(self):
        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = []
        self.assertEqual(notified,set(expected_notified))

        issue.assigned_to = self.user1
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = []
        self.assertEqual(notified,set(expected_notified))

        issue.assigned_to = self.user2
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user2]
        self.assertEqual(notified,set(expected_notified))

        issue.delete()

    def test_issue_with_owner_notification(self):
        self.user1.notify_changes_by_me = True
        self.user1.save()

        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user1]
        self.assertEqual(notified,set(expected_notified))

        issue.assigned_to = self.user1
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user1]
        self.assertEqual(notified,set(expected_notified))

        issue.assigned_to = self.user2
        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user1, self.user2]
        self.assertEqual(notified,set(expected_notified))

        issue.delete()

        self.user1.notify_changes_by_me = False
        self.user1.save()

class OnlyOwnerNotificationsTestCase(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user4 = create_user(4)
        self.user5 = create_user(5)

        self.user1.notify_level = "only_owner"
        self.user1.save()
        self.user2.notify_level = "only_owner"
        self.user2.save()
        self.user3.notify_level = "only_owner"
        self.user3.save()
        self.user4.notify_level = "only_owner"
        self.user4.save()
        self.user5.notify_level = "only_owner"
        self.user5.save()

        self.project1 = create_project(1, self.user1)

        add_membership(self.project1, self.user1, "back")
        add_membership(self.project1, self.user2, "back")
        add_membership(self.project1, self.user3, "back")
        add_membership(self.project1, self.user4, "back")
        add_membership(self.project1, self.user5, "back")

    def test_issue(self):
        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user2)
        expected_notified = [self.user1]
        self.assertEqual(notified,set(expected_notified))

        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = []
        self.assertEqual(notified,set(expected_notified))

        issue.owner = self.user2
        notified = issue.get_watchers_to_notify(self.user2)
        expected_notified = []
        self.assertEqual(notified,set(expected_notified))

        issue.delete()

    def test_issue_with_owner_notification(self):
        self.user1.notify_changes_by_me = True
        self.user1.save()

        issue = create_issue(1, self.user1, self.project1)
        notified = issue.get_watchers_to_notify(self.user2)
        expected_notified = [self.user1]
        self.assertEqual(notified,set(expected_notified))

        notified = issue.get_watchers_to_notify(self.user1)
        expected_notified = [self.user1]
        self.assertEqual(notified,set(expected_notified))

        issue.owner = self.user2
        notified = issue.get_watchers_to_notify(self.user2)
        expected_notified = []
        self.assertEqual(notified,set(expected_notified))

        issue.delete()

        self.user1.notify_changes_by_me = False
        self.user1.save()
