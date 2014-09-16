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
