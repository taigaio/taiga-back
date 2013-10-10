# -*- coding: utf-8 -*-


from django.db.models.loading import get_model


def create_issue(id, owner, project, milestone=None, save=True):
    model = get_model("issues", "Issue")

    instance = model(
       subject="Issue {0}".format(id),
       description="The issue description.",
       project=project,
       milestone=milestone,
       status=project.issue_statuses.all()[0],
       severity=project.severities.all()[0],
       priority=project.priorities.all()[0],
       type=project.issue_types.all()[0],
       owner=owner
    )

    if save:
        instance.save()
    return instance
