import json
from django import test

from taiga.users.tests import create_user
from taiga.projects.tests import create_project

from .. import services
from .. import models
from . import create_userstory


class UserStoriesServiceTestCase(test.TestCase):
    fixtures = ["initial_domains.json"]

    def setUp(self):
        self.user1 = create_user(1) # Project owner
        self.project1 = create_project(1, self.user1)

    def test_bulk_insert(self):
        model = models.UserStory
        self.assertEqual(model.objects.count(), 0)

        service = services.UserStoriesService()
        service.bulk_insert(self.project1, self.user1, "kk1\nkk2\n")

        self.assertEqual(model.objects.count(), 2)

    def test_bulk_order_update(self):
        userstory1 = create_userstory(1, self.user1, self.project1)
        userstory2 = create_userstory(2, self.user1, self.project1)

        data = [
            [userstory1.id, 20],
            [userstory2.id, 30],
        ]

        service = services.UserStoriesService()
        service.bulk_update_order(self.project1, self.user1, data)

        model = models.UserStory
        userstory1 = model.objects.get(pk=userstory1.id)
        userstory2 = model.objects.get(pk=userstory2.id)

        self.assertEqual(userstory1.order, 20)
        self.assertEqual(userstory2.order, 30)
