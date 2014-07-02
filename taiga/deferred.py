from django.conf import settings

from .celery import app


def _send_task(task, args, kwargs, **options):
    if settings.CELERY_ALWAYS_EAGER:
        return app.tasks[task].apply(args, kwargs, **options)
    return app.send_task(task, args, kwargs, **options)


def defer(task: str, *args, **kwargs):
    """Defer the execution of a task.

    Defer the execution of a task and returns a future objects with the following methods among
    others:
    - `failed()` Returns `True` if the task failed.
    - `ready()` Returns `True` if the task has been executed.
    - `forget()` Forget about the result.
    - `get()` Wait until the task is ready and return its result.
    - `result` When the task has been executed the result is in this attribute.
    More info at Celery docs on `AsyncResult` object.

    :param task: Name of the task to execute.

    :return: A future object.
    """
    return _send_task(task, args, kwargs, routing_key="transient.deferred")


def call_async(task: str, *args, **kwargs):
    """Run a task and ignore its result.

    This is just a star argument version of `apply_async`.

    :param task: Name of the task to execute.
    :param args: Arguments for the task.
    :param kwargs: Keyword arguments for the task.
    """
    apply_async(task, args, kwargs)


def apply_async(task: str, args=None, kwargs=None, **options):
    """Run a task and ignore its result.

    :param task: Name of the task to execute.
    :param args: Tupple of arguments for the task.
    :param kwargs: Dict of keyword arguments for the task.
    :param options: Celery-specific options when running the task. See Celery docs on `apply_async`
    """
    _send_task(task, args, kwargs, **options)
