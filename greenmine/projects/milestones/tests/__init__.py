# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_milestone(id, owner, project, save=True):
    model = get_model("milestones", "Milestone")

    instance = model(
       name="Milestone {0}".format(id),
       project=project,
       owner=owner
    )

    if save:
        instance.save()
    return instance
