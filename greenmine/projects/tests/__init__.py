# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_project(id, owner, save=True):
    model = get_model("projects", "Project")

    instance = model(
       name="Project {0}".format(id),
       description="This is a test project",
       owner=owner,
       total_story_points=id
    )

    if save:
        instance.save()
    return instance


def add_membership(project, user, role_slug="back"):
    model = get_model("users", "Role")
    role = model.objects.get(slug=role_slug)

    model = get_model("projects", "Membership")
    instance = model.objects.create(
        project=project,
        user=user,
        role=role
    )
    return instance
