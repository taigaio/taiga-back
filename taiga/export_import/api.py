from rest_framework.response import Response
from rest_framework import status

from taiga.base.api.mixins import CreateModelMixin
from taiga.base.api.viewsets import GenericViewSet
from taiga.base.decorators import detail_route
from taiga.projects.models import Project

from . import serializers
from . import service
from . import permissions

from django.db.models import signals

def __disconnect_signals():
    signals.pre_save.receivers = []
    signals.post_save.receivers = []

class ProjectImporterViewSet(CreateModelMixin, GenericViewSet):
    model = Project
    permission_classes = (permissions.ImportPermission, )

    def create(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_project', None)

        data = request.DATA.copy()
        if not data['owner']:
            data['owner'] = request.user

        project_serialized = service.store_project(data)

        if project_serialized:
            service.store_choices(project_serialized.object, data, "points", project_serialized.object.points, serializers.PointsExportSerializer, "default_points")
            service.store_choices(project_serialized.object, data, "issue_types", project_serialized.object.issue_types, serializers.IssueTypeExportSerializer, "default_issue_type")
            service.store_choices(project_serialized.object, data, "issue_statuses", project_serialized.object.issue_statuses, serializers.IssueStatusExportSerializer, "default_issue_status")
            service.store_choices(project_serialized.object, data, "us_statuses", project_serialized.object.us_statuses, serializers.UserStoryStatusExportSerializer, "default_us_status")
            service.store_choices(project_serialized.object, data, "task_statuses", project_serialized.object.task_statuses, serializers.TaskStatusExportSerializer, "default_task_status")
            service.store_choices(project_serialized.object, data, "priorities", project_serialized.object.priorities, serializers.PriorityExportSerializer, "default_priority")
            service.store_choices(project_serialized.object, data, "severities", project_serialized.object.severities, serializers.SeverityExportSerializer, "default_severity")
            service.store_default_choices(project_serialized.object, data)
            service.store_roles(project_serialized.object, data)
            service.store_memberships(project_serialized.object, data)
            headers = self.get_success_headers(project_serialized.data)
            return Response(project_serialized.data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(service.get_errors(), status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def issue(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_item', serializer.object)

    @detail_route(methods=['post'])
    def task(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_item', serializer.object)

    @detail_route(methods=['post'])
    def us(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_item', serializer.object)

    @detail_route(methods=['post'])
    def wiki_page(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_item', serializer.object)

    @detail_route(methods=['post'])
    def wiki_link(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_item', serializer.object)
