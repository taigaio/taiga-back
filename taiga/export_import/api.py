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

from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status

from django.utils.decorators import method_decorator
from django.db.transaction import atomic
from django.db.models import signals

from taiga.base.api.mixins import CreateModelMixin
from taiga.base.api.viewsets import GenericViewSet
from taiga.base.decorators import detail_route
from taiga.projects.models import Project, Membership
from taiga.projects.issues.models import Issue

from . import serializers
from . import service
from . import permissions


class Http400(APIException):
    status_code = 400


class ProjectImporterViewSet(CreateModelMixin, GenericViewSet):
    model = Project
    permission_classes = (permissions.ImportPermission, )

    @method_decorator(atomic)
    def create(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_project', None)

        data = request.DATA.copy()
        data['owner'] = data.get('owner', request.user.email)

        project_serialized = service.store_project(data)

        if project_serialized is None:
            raise Http400(service.get_errors())

        if "points" in data:
            service.store_choices(project_serialized.object, data,
                                  "points", serializers.PointsExportSerializer)
        if "issue_types" in data:
            service.store_choices(project_serialized.object, data,
                                  "issue_types",
                                  serializers.IssueTypeExportSerializer)
        if "issue_statuses" in data:
            service.store_choices(project_serialized.object, data,
                                  "issue_statuses",
                                  serializers.IssueStatusExportSerializer,)
        if "us_statuses" in data:
            service.store_choices(project_serialized.object, data,
                                  "us_statuses",
                                  serializers.UserStoryStatusExportSerializer,)
        if "task_statuses" in data:
            service.store_choices(project_serialized.object, data,
                                  "task_statuses",
                                  serializers.TaskStatusExportSerializer)
        if "priorities" in data:
            service.store_choices(project_serialized.object, data,
                                  "priorities",
                                  serializers.PriorityExportSerializer)
        if "severities" in data:
            service.store_choices(project_serialized.object, data,
                                  "severities",
                                  serializers.SeverityExportSerializer)

        if ("points" in data or "issues_types" in data or
                "issues_statuses" in data or "us_statuses" in data or
                "task_statuses" in data or "priorities" in data or
                "severities" in data):
            service.store_default_choices(project_serialized.object, data)

        if "roles" in data:
            service.store_roles(project_serialized.object, data)

        if "memberships" in data:
            service.store_memberships(project_serialized.object, data)

        if project_serialized.object.memberships.filter(user=project_serialized.object.owner).count() == 0:
            if project_serialized.object.roles.all().count() > 0:
                Membership.objects.create(
                    project=project_serialized.object,
                    email=project_serialized.object.owner.email,
                    user=project_serialized.object.owner,
                    role=project_serialized.object.roles.all().first(),
                    is_owner=True
                )

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        response_data = project_serialized.data
        response_data['id'] = project_serialized.object.id
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def issue(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        signals.pre_save.disconnect(sender=Issue,
            dispatch_uid="set_finished_date_when_edit_issue")

        issue = service.store_issue(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(issue.data)
        return Response(issue.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def task(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        task = service.store_task(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(task.data)
        return Response(task.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def us(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        us = service.store_user_story(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(us.data)
        return Response(us.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def milestone(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        milestone = service.store_milestone(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(milestone.data)
        return Response(milestone.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def wiki_page(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        wiki_page = service.store_wiki_page(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(wiki_page.data)
        return Response(wiki_page.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def wiki_link(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        wiki_link = service.store_wiki_link(project, request.DATA.copy())

        errors = service.get_errors()
        if errors:
            raise Http400(errors)

        headers = self.get_success_headers(wiki_link.data)
        return Response(wiki_link.data, status=status.HTTP_201_CREATED, headers=headers)
