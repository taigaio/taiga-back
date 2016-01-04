# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from unittest import mock

from taiga import celery
from taiga.deferred import defer, call_async, apply_async


def test_defer():
    # settings.CELERY_ALWAYS_EAGER = True
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    with mock.patch("taiga.deferred.app") as app:
        defer(name, *args, **kwargs)
        app.tasks[name].apply.assert_called_once_with(args, kwargs,
                                                      routing_key="transient.deferred")


def test_apply_async():
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    with mock.patch("taiga.deferred.app") as app:
        apply_async(name, args, kwargs)
        app.tasks[name].apply.assert_called_once_with(args, kwargs)


def test_call_async():
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    with mock.patch("taiga.deferred.app") as app:
        call_async(name, *args, **kwargs)
        app.tasks[name].apply.assert_called_once_with(args, kwargs)


def test_task_invocation():
    celery.app.task(name="_test_task")(lambda: 1)
    assert defer("_test_task").get() == 1
