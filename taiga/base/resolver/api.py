# -*- coding: utf-8 -*-

# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db.models.loading import get_model

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from taiga.base import exceptions as excp


class ResolverViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        project_model = get_model("projects", "Project")
        userstory_model = get_model("userstories", "UserStory")
        task_model = get_model("tasks", "Task")
        issue_model = get_model("issues", "Issue")
        milestone_model = get_model("milestones", "Milestone")

        project_slug = request.QUERY_PARAMS.get('project', None)
        us_ref = request.QUERY_PARAMS.get('us', None)
        task_ref = request.QUERY_PARAMS.get('task', None)
        issue_ref = request.QUERY_PARAMS.get('issue', None)
        milestone_slug = request.QUERY_PARAMS.get('milestone', None)

        if project_slug is None:
            return Response({})

        try:
            project = project_model.objects.get(slug=project_slug)
        except project_model.DoesNotExist:
            return Response({})

        result = {"project": project.id}

        if us_ref is not None:
            try:
                us = project.user_stories.get(ref=us_ref)
                result["us"] = us.id
            except userstory_model.DoesNotExist:
                pass

        if task_ref is not None:
            try:
                task = project.tasks.get(ref=task_ref)
                result["task"] = task.id
            except task_model.DoesNotExist:
                pass

        if issue_ref is not None:
            try:
                issue = project.issues.get(ref=issue_ref)
                result["issue"] = issue.id
            except issue_model.DoesNotExist:
                pass

        if milestone_slug is not None:
            try:
                milestone = project.milestones.get(slug=milestone_slug)
                result["milestone"] = milestone.id
            except milestone_model.DoesNotExist:
                pass

        return Response(result)
