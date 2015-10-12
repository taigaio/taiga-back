# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Anler Hernández <hello@anler.me>
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


import pytest

from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task

from tests import factories as f
pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.us_closed_status = f.UserStoryStatusFactory(is_closed=True)
    m.us_open_status = f.UserStoryStatusFactory(is_closed=False)
    m.task_closed_status = f.TaskStatusFactory(is_closed=True)
    m.task_open_status = f.TaskStatusFactory(is_closed=False)
    m.user_story1 = f.UserStoryFactory(status=m.us_open_status)
    m.user_story2 = f.UserStoryFactory(status=m.us_open_status)
    m.task1 = f.TaskFactory(user_story=m.user_story1, status=m.task_open_status)
    m.task2 = f.TaskFactory(user_story=m.user_story1, status=m.task_open_status)
    m.task3 = f.TaskFactory(user_story=m.user_story1, status=m.task_open_status)
    return m


def test_auto_close_us_when_change_us_status_to_closed_without_tasks(data):
    assert data.user_story2.is_closed is False
    data.user_story2.status = data.us_closed_status
    data.user_story2.save()
    data.user_story2 = UserStory.objects.get(pk=data.user_story2.pk)
    assert data.user_story2.is_closed is True
    data.user_story2.status = data.us_open_status
    data.user_story2.save()
    data.user_story2 = UserStory.objects.get(pk=data.user_story2.pk)
    assert data.user_story2.is_closed is False


def test_noop_when_change_us_status_to_closed_with_open_tasks(data):
    assert data.user_story1.is_closed is False
    data.user_story1.status = data.us_closed_status
    data.user_story1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False
    data.user_story1.status = data.us_open_status
    data.user_story1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False


def test_auto_close_us_with_closed_state_when_all_tasks_are_deleted(data):
    data.user_story1.status = data.us_closed_status
    data.user_story1.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task3.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task2.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task1.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True


def test_auto_open_us_with_open_status_when_all_tasks_are_deleted(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    data.task3.status = data.task_closed_status
    data.task3.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task3.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task2.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task1.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False


def test_auto_open_us_with_open_status_when_all_task_are_moved_to_another_us(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    data.task3.status = data.task_closed_status
    data.task3.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task3.user_story = data.user_story2
    data.task3.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task2.user_story = data.user_story2
    data.task2.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task1.user_story = data.user_story2
    data.task1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False


def test_auto_close_us_closed_status_when_all_tasks_are_moved_to_another_us(data):
    data.user_story1.status = data.us_closed_status
    data.user_story1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task3.user_story = data.user_story2
    data.task3.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task2.user_story = data.user_story2
    data.task2.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task1.user_story = data.user_story2
    data.task1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True


def test_auto_close_us_when_tasks_are_gradually_reopened(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    data.task3.status = data.task_closed_status
    data.task3.save()

    assert data.user_story1.is_closed is True

    data.task3.status = data.task_open_status
    data.task3.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task2.status = data.task_open_status
    data.task2.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task1.status = data.task_open_status
    data.task1.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False


def test_auto_close_us_after_open_task_is_deleted(data):
    """
    User story should be in closed state after
    delete the unique open task.
    """
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    assert data.user_story1.is_closed is False
    data.task3.delete()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True


def test_auto_close_userstory_with_milestone_when_task_and_milestone_are_removed(data):
    milestone = f.MilestoneFactory.create()

    data.task1.status = data.task_closed_status
    data.task1.milestone = milestone
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.milestone = milestone
    data.task2.save()
    data.task3.status = data.task_open_status
    data.task3.milestone = milestone
    data.task3.save()
    data.user_story1.milestone = milestone
    data.user_story1.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False

    data.task3 = Task.objects.get(pk=data.task3.pk)
    milestone.delete()
    data.task3.delete()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True


def test_auto_close_us_when_all_tasks_are_changed_to_close_status(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    assert data.user_story1.is_closed is False
    data.task3.user_story = data.user_story2
    data.task3.save()
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True


def test_auto_open_us_when_add_open_task(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    data.task3.user_story = data.user_story2
    data.task3.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    data.task3.user_story = data.user_story1
    data.task3.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False


def test_task_create(data):
    data.task1.status = data.task_closed_status
    data.task1.save()
    data.task2.status = data.task_closed_status
    data.task2.save()
    data.task3.status = data.task_closed_status
    data.task3.save()

    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    f.TaskFactory(user_story=data.user_story1, status=data.task_closed_status)
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is True

    f.TaskFactory(user_story=data.user_story1, status=data.task_open_status)
    data.user_story1 = UserStory.objects.get(pk=data.user_story1.pk)
    assert data.user_story1.is_closed is False
