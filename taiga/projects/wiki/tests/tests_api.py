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
from django.core import mail
from django.core.urlresolvers import reverse

from taiga.users.tests import create_user
from taiga.projects.tests import create_project, add_membership
from taiga.projects.wiki.models import WikiPage

from . import create_wiki_page


class WikiPagesTestCase(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1)
        self.user2 = create_user(2)
        self.user3 = create_user(3)
        self.user4 = create_user(4)

        self.project1 = create_project(1, self.user1)
        add_membership(self.project1, self.user2)
        add_membership(self.project1, self.user3)

        self.project2 = create_project(2, self.user4)

        self.wiki_page1 = create_wiki_page(1, self.user2, self.project1)
        self.wiki_page2 = create_wiki_page(2, self.user2, self.project1)

    def test_list_wiki_pages_by_anon(self):
        response = self.client.get(reverse("wiki-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_wiki_pages_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-list"))
        self.assertEqual(response.status_code, 200)
        wiki_pages_list = response.data
        self.assertEqual(len(wiki_pages_list), 2)
        self.client.logout()

    def test_list_wiki_pages_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-list"))
        self.assertEqual(response.status_code, 200)
        wiki_pages_list = response.data
        self.assertEqual(len(wiki_pages_list), 2)
        self.client.logout()

    def test_list_wiki_pages_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-list"))
        self.assertEqual(response.status_code, 200)
        wiki_pages_list = response.data
        self.assertEqual(len(wiki_pages_list), 2)
        self.client.logout()

    def test_list_wiki_pages_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-list"))
        self.assertEqual(response.status_code, 200)
        wiki_pages_list = response.data
        self.assertEqual(len(wiki_pages_list), 0)
        self.client.logout()

    def test_view_wiki_page_by_anon(self):
        response = self.client.get(reverse("wiki-detail", args=(self.wiki_page1.id,)))
        self.assertEqual(response.status_code, 401)

    def test_view_wiki_page_by_project_owner(self):
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-detail", args=(self.wiki_page1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_wiki_page_by_owner(self):
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-detail", args=(self.wiki_page1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_wiki_page_by_membership(self):
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-detail", args=(self.wiki_page1.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_view_wiki_page_by_no_membership(self):
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.get(reverse("wiki-detail", args=(self.wiki_page1.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()


    def test_create_wiki_page_by_anon(self):
        data = {
            "slug": "test-wiki-page",
            "content": "Test WikiPage",
            "project": self.project1.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.post(
            reverse("wiki-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(WikiPage.objects.all().count(), 2)

    def test_create_wiki_page_by_project_owner(self):
        data = {
            "slug": "test-wiki-page",
            "content": "Test WikiPage",
            "project": self.project1.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("wiki-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WikiPage.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_create_wiki_page_by_membership(self):
        data = {
            "slug": "test-wiki-page",
            "content": "Test WikiPage",
            "project": self.project1.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("wiki-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WikiPage.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_create_wiki_page_by_membership_with_wron_project(self):
        data = {
            "slug": "test-wiki-page",
            "content": "Test WikiPage",
            "project": self.project2.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("wiki-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_create_wiki_page_by_no_membership(self):
        data = {
            "slug": "test-wiki-page",
            "content": "Test WikiPage",
            "project": self.project1.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.post(
            reverse("wiki-list"),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_edit_wiki_page_by_anon(self):
        data = {
            "content": "Edited test wiki_page",
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertNotEqual(data["content"], self.wiki_page1.content)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(WikiPage.objects.all().count(), 2)

    def test_edit_wiki_page_by_project_owner(self):
        data = {
            "content": "Edited test wiki_page",
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertNotEqual(data["content"], self.wiki_page1.content)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["content"], response.data["content"])
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_edit_wiki_page_by_project_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_edit_wiki_page_by_owner(self):
        data = {
            "content": "Edited test wiki_page",
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertNotEqual(data["content"], self.wiki_page1.content)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["content"], response.data["content"])
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_edit_wiki_page_by_owner_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_edit_wiki_page_by_membership(self):
        data = {
            "content": "Edited test wiki_page",
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertNotEqual(data["content"], self.wiki_page1.content)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["content"], response.data["content"])
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()

    def test_edit_wiki_page_by_membership_with_wron_project(self):
        data = {
            "project": self.project2.id
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_edit_wiki_page_by_no_membership(self):
        data = {
            "content": "Edited test wiki_page",
        }

        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.assertNotEqual(data["content"], self.wiki_page1.content)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.patch(
            reverse("wiki-detail", args=(self.wiki_page1.id,)),
            json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

    def test_delete_wiki_page_by_ano(self):
        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.delete(
                reverse("wiki-detail", args=(self.wiki_page1.id,))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(WikiPage.objects.all().count(), 2)

    def test_delete_wiki_page_by_project_owner(self):
        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("wiki-detail", args=(self.wiki_page1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(WikiPage.objects.all().count(), 1)
        self.client.logout()

    def test_delete_wiki_page_by_owner(self):
        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user2.username,
                                     password=self.user2.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("wiki-detail", args=(self.wiki_page1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(WikiPage.objects.all().count(), 1)
        self.client.logout()

    def test_delete_wiki_page_by_membership(self):
        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user3.username,
                                     password=self.user3.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("wiki-detail", args=(self.wiki_page1.id,))
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(WikiPage.objects.all().count(), 1)
        self.client.logout()

    def test_delete_wiki_page_by_no_membership(self):
        self.assertEqual(WikiPage.objects.all().count(), 2)
        response = self.client.login(username=self.user4.username,
                                     password=self.user4.username)
        self.assertTrue(response)
        response = self.client.delete(
                reverse("wiki-detail", args=(self.wiki_page1.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(WikiPage.objects.all().count(), 2)
        self.client.logout()

