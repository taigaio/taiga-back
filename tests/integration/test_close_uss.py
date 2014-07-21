# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

from unittest.mock import patch, MagicMock, call

from django.core.exceptions import ValidationError

from tests import factories

from taiga.projects.userstories.models import UserStory

import pytest

pytestmark = pytest.mark.django_db


def test_us_without_tasks_close():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)
    user_story = factories.UserStoryFactory(status=open_status)
    assert user_story.is_closed == False
    user_story.status = closed_status
    user_story.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == True


def test_us_without_tasks_open():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)
    user_story = factories.UserStoryFactory(status=closed_status)
    assert user_story.is_closed == True
    user_story.status = open_status
    user_story.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == False


def test_us_with_tasks_close():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)

    closed_task_status = factories.TaskStatusFactory(is_closed=True)
    open_task_status = factories.TaskStatusFactory(is_closed=False)

    user_story = factories.UserStoryFactory(status=closed_status)
    task1 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    task2 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    task3 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    assert user_story.is_closed == True
    user_story.status = open_status
    user_story.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == True


def test_us_with_tasks_on_delete_empty_open():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)

    closed_task_status = factories.TaskStatusFactory(is_closed=True)
    open_task_status = factories.TaskStatusFactory(is_closed=False)

    user_story = factories.UserStoryFactory(status=open_status)
    task1 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    assert user_story.is_closed == True
    task1.delete()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == False


def test_us_with_tasks_on_delete_empty_close():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)

    closed_task_status = factories.TaskStatusFactory(is_closed=True)
    open_task_status = factories.TaskStatusFactory(is_closed=False)

    user_story = factories.UserStoryFactory(status=closed_status)
    task1 = factories.TaskFactory(user_story=user_story, status=open_task_status)
    assert user_story.is_closed == False
    task1.delete()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == True


def test_us_with_tasks_open():
    closed_status = factories.UserStoryStatusFactory(is_closed=True)
    open_status = factories.UserStoryStatusFactory(is_closed=False)

    closed_task_status = factories.TaskStatusFactory(is_closed=True)
    open_task_status = factories.TaskStatusFactory(is_closed=False)

    user_story = factories.UserStoryFactory(status=open_status)
    task1 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    task2 = factories.TaskFactory(user_story=user_story, status=closed_task_status)
    task3 = factories.TaskFactory(user_story=user_story, status=open_task_status)
    assert user_story.is_closed == False
    user_story.status = closed_status
    user_story.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == False


def test_us_close_last_tasks():
    closed_status = factories.TaskStatusFactory(is_closed=True)
    open_status = factories.TaskStatusFactory(is_closed=False)
    user_story = factories.UserStoryFactory()
    task1 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task2 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task3 = factories.TaskFactory(user_story=user_story, status=open_status)
    assert user_story.is_closed == False
    task3.status = closed_status
    task3.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == True


def test_us_with_all_closed_open_task():
    closed_status = factories.TaskStatusFactory(is_closed=True)
    open_status = factories.TaskStatusFactory(is_closed=False)
    user_story = factories.UserStoryFactory()
    task1 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task2 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task3 = factories.TaskFactory(user_story=user_story, status=closed_status)
    assert user_story.is_closed == True
    task3.status = open_status
    task3.save()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == False


def test_us_delete_task_then_all_closed():
    closed_status = factories.TaskStatusFactory(is_closed=True)
    open_status = factories.TaskStatusFactory(is_closed=False)
    user_story = factories.UserStoryFactory()
    task1 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task2 = factories.TaskFactory(user_story=user_story, status=closed_status)
    task3 = factories.TaskFactory(user_story=user_story, status=open_status)
    assert user_story.is_closed == False
    task3.delete()
    user_story = UserStory.objects.get(pk=user_story.pk)
    assert user_story.is_closed == True


def test_us_change_task_us_then_all_closed():
    closed_status = factories.TaskStatusFactory(is_closed=True)
    open_status = factories.TaskStatusFactory(is_closed=False)
    user_story1 = factories.UserStoryFactory()
    user_story2 = factories.UserStoryFactory()
    task1 = factories.TaskFactory(user_story=user_story1, status=closed_status)
    task2 = factories.TaskFactory(user_story=user_story1, status=closed_status)
    task3 = factories.TaskFactory(user_story=user_story1, status=open_status)
    assert user_story1.is_closed == False
    task3.user_story = user_story2
    task3.save()
    user_story1 = UserStory.objects.get(pk=user_story1.pk)
    assert user_story1.is_closed == True


def test_us_change_task_us_to_us_with_all_closed():
    closed_status = factories.TaskStatusFactory(is_closed=True)
    open_status = factories.TaskStatusFactory(is_closed=False)
    user_story1 = factories.UserStoryFactory()
    user_story2 = factories.UserStoryFactory()
    task1 = factories.TaskFactory(user_story=user_story1, status=closed_status)
    task2 = factories.TaskFactory(user_story=user_story1, status=closed_status)
    task3 = factories.TaskFactory(user_story=user_story2, status=open_status)
    assert user_story1.is_closed == True
    task3.user_story = user_story1
    task3.save()
    user_story1 = UserStory.objects.get(pk=user_story1.pk)
    assert user_story1.is_closed == False
