# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps

from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.api import viewsets
from taiga.base.api.utils import get_object_or_404
from taiga.permissions.services import user_has_perm

from .validators import ResolverValidator
from . import permissions


class ResolverViewSet(viewsets.ViewSet):
    permission_classes = (permissions.ResolverPermission,)

    def list(self, request, **kwargs):
        validator = ResolverValidator(data=request.QUERY_PARAMS)
        if not validator.is_valid():
            raise exc.BadRequest(validator.errors)

        data = validator.data

        project_model = apps.get_model("projects", "Project")
        project = get_object_or_404(project_model, slug=data["project"])

        self.check_permissions(request, "list", project)

        result = {"project": project.pk}

        if data["us"] and user_has_perm(request.user, "view_us", project):
            result["us"] = get_object_or_404(project.user_stories.all(),
                                             ref=data["us"]).pk
        if data["task"] and user_has_perm(request.user, "view_tasks", project):
            result["task"] = get_object_or_404(project.tasks.all(),
                                               ref=data["task"]).pk
        if data["issue"] and user_has_perm(request.user, "view_issues", project):
            result["issue"] = get_object_or_404(project.issues.all(),
                                                ref=data["issue"]).pk
        if data["milestone"] and user_has_perm(request.user, "view_milestones", project):
            result["milestone"] = get_object_or_404(project.milestones.all(),
                                                    slug=data["milestone"]).pk
        if data["wikipage"] and user_has_perm(request.user, "view_wiki_pages", project):
            result["wikipage"] = get_object_or_404(project.wiki_pages.all(),
                                                   slug=data["wikipage"]).pk

        if data["ref"]:
            ref_found = False  # No need to continue once one ref is found
            if user_has_perm(request.user, "view_us", project):
                us = project.user_stories.filter(ref=data["ref"]).first()
                if us:
                    result["us"] = us.pk
                    ref_found = True
            if ref_found is False and user_has_perm(request.user, "view_tasks", project):
                task = project.tasks.filter(ref=data["ref"]).first()
                if task:
                    result["task"] = task.pk
                    ref_found = True
            if ref_found is False and user_has_perm(request.user, "view_issues", project):
                issue = project.issues.filter(ref=data["ref"]).first()
                if issue:
                    result["issue"] = issue.pk

        return response.Ok(result)
