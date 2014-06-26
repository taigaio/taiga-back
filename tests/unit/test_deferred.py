from unittest import mock
from taiga.deferred import defer, call_async, apply_async


@mock.patch("taiga.deferred.app")
def test_defer(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    defer(name, *args, **kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs, routing_key="transient.deferred")


@mock.patch("taiga.deferred.app")
def test_apply_async(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    apply_async(name, args, kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs)


@mock.patch("taiga.deferred.app")
def test_call_async(app):
    name = "task name"
    args = (1, 2)
    kwargs = {"kw": "keyword argument"}

    call_async(name, *args, **kwargs)

    app.send_task.assert_called_once_with(name, args, kwargs)
