# -*- coding: utf-8 -*-


from django.db.models.loading import get_model


def create_userstory(id, owner, project, milestone=None, save=True):
    model = get_model("userstories", "UserStory")

    instance = model(
       subject="User Story {0}".format(id),
       description="The US description.",
       project=project,
       milestone=milestone,
       status=project.us_statuses.all()[0],
       owner=owner
    )

    if save:
        instance.save()
    return instance
