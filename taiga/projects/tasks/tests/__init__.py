# -*- coding: utf-8 -*-


from django.db.models.loading import get_model


def create_task(id, owner, project, milestone=None, user_story=None, save=True):
    model = get_model("tasks", "Task")

    instance = model(
       subject="Task {0}".format(id),
       description="The Task description.",
       project=project,
       milestone=milestone,
       user_story=user_story,
       status=project.task_statuses.all()[0],
       owner=owner
    )

    if save:
        instance.save()
    return instance
