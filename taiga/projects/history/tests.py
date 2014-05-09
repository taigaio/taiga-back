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

from django import test
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model

from taiga.users.tests import create_user
from taiga.projects.tests import create_project
from taiga.projects.userstories.tests import create_userstory

from . import services as history
from . import models


class HistoryApiViewsTest(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1) # Project owner
        self.project1 = create_project(1, self.user1)

    def test_resolve_urls(self):
        self.assertEqual(reverse("userstory-history-detail", args=[1]), "/api/v1/history/userstory/1")

    def test_list_history_entries(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        userstory1.subject = "test1"
        userstory1.save()

        history.take_snapshot(userstory1)
        userstory1.subject = "test2"
        userstory1.save()

        history.take_snapshot(userstory1)

        response = self.client.login(username=self.user1.username,
                                     password=self.user1.username)

        url = reverse("userstory-history-detail", args=[userstory1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)



class HistoryServicesTest(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user1 = create_user(1) # Project owner
        self.project1 = create_project(1, self.user1)

    # def test_freeze_userstory(self):
    #     userstory1 = create_userstory(1, self.user1, self.project1)
    #     fobj = history.freeze_model_instance(userstory1)

    #     self.assertEqual(fobj.key, "userstories.userstory:{}".format(userstory1.id))
    #     self.assertIn("status", fobj.snapshot)

    def test_freeze_wrong_object(self):
        some_object = object()
        with self.assertRaises(Exception):
            history.freeze_model_instance(some_object)

    def test_diff(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        userstory1.subject = "test1"
        userstory1.save()

        fobj1 = history.freeze_model_instance(userstory1)

        userstory1.subject = "test2"
        userstory1.save()

        fobj2 = history.freeze_model_instance(userstory1)

        fdiff = history.make_diff(fobj1, fobj2)
        self.assertEqual(fdiff.diff, {"subject": ('test1', 'test2')})

    def test_snapshot(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        userstory1.subject = "test1"
        userstory1.save()

        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test2"
        userstory1.save()

        self.assertEqual(hentry.key, "userstories.userstory:{}".format(userstory1.id))
        self.assertEqual(models.HistoryEntry.objects.count(), 1)

        history.take_snapshot(userstory1)
        self.assertEqual(models.HistoryEntry.objects.count(), 2)

    def test_comment(self):
        userstory1 = create_userstory(1, self.user1, self.project1)

        self.assertEqual(models.HistoryEntry.objects.count(), 0)
        hentry = history.take_snapshot(userstory1, comment="Sample comment")

        self.assertEqual(models.HistoryEntry.objects.count(), 1)
        self.assertEqual(hentry.comment, "Sample comment")

    def test_userstory_points(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        hentry = history.take_snapshot(userstory1)

        self.assertEqual({}, hentry.values_diff)

        rpmodel_cls = get_model("userstories", "RolePoints")
        pmodel_cls = get_model("projects", "Points")

        rolepoints = rpmodel_cls.objects.filter(user_story=userstory1)[0]
        points = pmodel_cls.objects.get(project=userstory1.project, value=15)

        rolepoints.points = points
        rolepoints.save()

        hentry = history.take_snapshot(userstory1)

        self.assertIn("points", hentry.values_diff)
        self.assertIn("UX", hentry.values_diff["points"])
        self.assertEqual(hentry.values_diff["points"]["UX"], ["?", "15"])

    def test_userstory_attachments(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        hentry = history.take_snapshot(userstory1)

        self.assertEqual({}, hentry.values_diff)

        # Create attachment file
        attachment_modelcls = get_model("attachments", "Attachment")

        content_type = ContentType.objects.get_for_model(userstory1.__class__)
        temporary_file = SimpleUploadedFile("text.txt", b"sample content")
        attachment = attachment_modelcls.objects.create(project=userstory1.project,
                                                        content_type=content_type,
                                                        content_object=userstory1,
                                                        object_id=userstory1.id,
                                                        owner=self.user1,
                                                        attached_file=temporary_file)

        hentry = history.take_snapshot(userstory1)
        self.assertIn("attachments", hentry.values_diff)

    def test_values(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        userstory1.subject = "test1"
        userstory1.save()

        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test2"
        userstory1.assigned_to = self.user1
        userstory1.save()

        hentry = history.take_snapshot(userstory1)

        self.assertIn("users", hentry.values)
        self.assertEqual(len(hentry.values), 1)
        self.assertIn("assigned_to", hentry.values_diff)
        self.assertEqual(hentry.values_diff["assigned_to"], [None, "Foo1 Bar1"])


    def test_partial_snapshots(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test1"
        userstory1.save()
        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test2"
        userstory1.save()
        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test3"
        userstory1.save()
        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test4"
        userstory1.save()
        hentry = history.take_snapshot(userstory1)

        userstory1.subject = "test5"
        userstory1.save()
        hentry = history.take_snapshot(userstory1)

        self.assertEqual(models.HistoryEntry.objects.count(), 6)
        self.assertEqual(models.HistoryEntry.objects.filter(is_snapshot=True).count(), 1)
        self.assertEqual(models.HistoryEntry.objects.filter(is_snapshot=False).count(), 5)
