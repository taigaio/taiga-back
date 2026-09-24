# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from taiga.base import response
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import detail_route
from taiga.projects.models import Project
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.services.promote import promote_to_us, demote_to_task

from . import validators


class PromoteToUserStoryMixin:
    """
    Promote an instance to User Story.
    """

    @detail_route(methods=["POST"])
    def promote_to_user_story(self, request, pk=None):
        validator = validators.PromoteToUserStoryValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        self.check_permissions(request, 'promote_to_us', project)

        obj = self.get_object()
        ret = promote_to_us(obj)
        self.persist_history_snapshot(obj=obj)

        # delete source task if required
        if isinstance(obj, Task):
            obj.delete()

        return response.Ok(ret)


class DemoteToTaskMixin:
    """
    Demote an instance to Task.
    """

    @detail_route(methods=["POST"])
    def demote_to_task(self, request, pk=None):
        validator = validators.DemoteToTaskValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        self.check_permissions(request, "demote_to_task", project)

        obj = self.get_object()

        if obj.project_id != project.id:
            return response.BadRequest(
                {"project_id": ("The user story doesn't belong to the given project.")}
            )

        if not obj.milestone_id and not data.get("milestone_id"):
            return response.BadRequest(
                {
                    "milestone_id": (
                        "This user story has no milestone. "
                        "Provide a milestone_id to avoid an orphaned task."
                    )
                }
            )

        ret = demote_to_task(obj, milestone_id=data.get("milestone_id"))
        self.persist_history_snapshot(obj=obj)

        # delete source UserStory if required
        if isinstance(obj, UserStory):
            obj.delete()

        return response.Ok(ret)
