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

from django.utils.translation import ugettext as _

from taiga.base.api.utils import get_object_or_404
from taiga.base import filters, response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.projects.models import Project, TaskStatus
from django.http import HttpResponse

from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.votes.mixins.viewsets import VotedResourceMixin, VotersViewSetMixin


from . import models
from . import permissions
from . import serializers
from . import services


class TaskViewSet(OCCResourceMixin, VotedResourceMixin, HistoryResourceMixin, WatchedResourceMixin,
                  BlockedByProjectMixin, ModelCrudViewSet):
    queryset = models.Task.objects.all()
    permission_classes = (permissions.TaskPermission,)
    filter_backends = (filters.CanViewTasksFilterBackend, filters.WatchersFilter)
    retrieve_exclude_filters = (filters.WatchersFilter,)
    filter_fields = ["user_story", "milestone", "project", "assigned_to",
        "status__is_closed"]

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.TaskNeighborsSerializer

        if self.action == "list":
            return serializers.TaskListSerializer

        return serializers.TaskSerializer

    def update(self, request, *args, **kwargs):
        self.object = self.get_object_or_none()
        project_id = request.DATA.get('project', None)
        if project_id and self.object and self.object.project.id != project_id:
            try:
                new_project = Project.objects.get(pk=project_id)
                self.check_permissions(request, "destroy", self.object)
                self.check_permissions(request, "create", new_project)

                sprint_id = request.DATA.get('milestone', None)
                if sprint_id is not None and new_project.milestones.filter(pk=sprint_id).count() == 0:
                    request.DATA['milestone'] = None

                us_id = request.DATA.get('user_story', None)
                if us_id is not None and new_project.user_stories.filter(pk=us_id).count() == 0:
                    request.DATA['user_story'] = None

                status_id = request.DATA.get('status', None)
                if status_id is not None:
                    try:
                        old_status = self.object.project.task_statuses.get(pk=status_id)
                        new_status = new_project.task_statuses.get(slug=old_status.slug)
                        request.DATA['status'] = new_status.id
                    except TaskStatus.DoesNotExist:
                        request.DATA['status'] = new_project.default_task_status.id

            except Project.DoesNotExist:
                return response.BadRequest(_("The project doesn't exist"))

        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.attach_votes_attrs_to_queryset(qs)
        qs = qs.select_related(
            "milestone",
            "owner",
            "assigned_to",
            "status",
            "project")

        return self.attach_watchers_attrs_to_queryset(qs)

    def pre_save(self, obj):
        if obj.user_story:
            obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions to set this sprint to this task."))

        if obj.user_story and obj.user_story.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions to set this user story to this task."))

        if obj.status and obj.status.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions to set this status to this task."))

        if obj.milestone and obj.user_story and obj.milestone != obj.user_story.milestone:
            raise exc.WrongArguments(_("You don't have permissions to set this sprint to this task."))

    @list_route(methods=["GET"])
    def by_ref(self, request):
        ref = request.QUERY_PARAMS.get("ref", None)
        project_id = request.QUERY_PARAMS.get("project", None)
        task = get_object_or_404(models.Task, ref=ref, project_id=project_id)
        return self.retrieve(request, pk=task.pk)

    @list_route(methods=["GET"])
    def csv(self, request):
        uuid = request.QUERY_PARAMS.get("uuid", None)
        if uuid is None:
            return response.NotFound()

        project = get_object_or_404(Project, tasks_csv_uuid=uuid)
        queryset = project.tasks.all().order_by('ref')
        data = services.tasks_to_csv(project, queryset)
        csv_response = HttpResponse(data.getvalue(), content_type='application/csv; charset=utf-8')
        csv_response['Content-Disposition'] = 'attachment; filename="tasks.csv"'
        return csv_response

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        serializer = serializers.TasksBulkSerializer(data=request.DATA)
        if serializer.is_valid():
            data = serializer.data
            project = Project.objects.get(id=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            if project.blocked_code is not None:
                raise exc.Blocked(_("Blocked element"))

            tasks = services.create_tasks_in_bulk(
                data["bulk_tasks"], milestone_id=data["sprint_id"], user_story_id=data["us_id"],
                status_id=data.get("status_id") or project.default_task_status_id,
                project=project, owner=request.user, callback=self.post_save, precall=self.pre_save)
            tasks_serialized = self.get_serializer_class()(tasks, many=True)

            return response.Ok(tasks_serialized.data)

        return response.BadRequest(serializer.errors)

    def _bulk_update_order(self, order_field, request, **kwargs):
        serializer = serializers.UpdateTasksOrderBulkSerializer(data=request.DATA)
        if not serializer.is_valid():
            return response.BadRequest(serializer.errors)

        data = serializer.data
        project = get_object_or_404(Project, pk=data["project_id"])

        self.check_permissions(request, "bulk_update_order", project)
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        services.update_tasks_order_in_bulk(data["bulk_tasks"],
                                            project=project,
                                            field=order_field)
        services.snapshot_tasks_in_bulk(data["bulk_tasks"], request.user)

        return response.NoContent()

    @list_route(methods=["POST"])
    def bulk_update_taskboard_order(self, request, **kwargs):
        return self._bulk_update_order("taskboard_order", request, **kwargs)

    @list_route(methods=["POST"])
    def bulk_update_us_order(self, request, **kwargs):
        return self._bulk_update_order("us_order", request, **kwargs)


class TaskVotersViewSet(VotersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.TaskVotersPermission,)
    resource_model = models.Task


class TaskWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.TaskWatchersPermission,)
    resource_model = models.Task
