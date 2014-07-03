from unittest import mock

from taiga import celery
from taiga.deferred import defer, call_async, apply_async

from ..utils import set_settings


@set_settings(CELERY_ALWAYS_EAGER=False)
@mock.patch("taiga.deferred.app")
def test_defer(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    defer(name, *args, **kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs, routing_key="transient.deferred")


@set_settings(CELERY_ALWAYS_EAGER=False)
@mock.patch("taiga.deferred.app")
def test_apply_async(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    apply_async(name, args, kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs)


@set_settings(CELERY_ALWAYS_EAGER=False)
@mock.patch("taiga.deferred.app")
def test_call_async(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    call_async(name, *args, **kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs)


@set_settings(CELERY_ALWAYS_EAGER=True)
def test_task_invocation():
    celery.app.task(name="_test_task")(lambda: 1)

    assert defer("_test_task").get() == 1
