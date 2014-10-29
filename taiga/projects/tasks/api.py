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

from django.utils.translation import ugettext_lazy as _

from taiga.base import filters, response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet
from taiga.projects.models import Project

from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.occ import OCCResourceMixin


from . import models
from . import permissions
from . import serializers
from . import services


class TaskViewSet(OCCResourceMixin, HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    model = models.Task
    serializer_class = serializers.TaskNeighborsSerializer
    list_serializer_class = serializers.TaskSerializer
    permission_classes = (permissions.TaskPermission,)
    filter_backends = (filters.CanViewTasksFilterBackend,)
    filter_fields = ["user_story", "milestone", "project"]

    def pre_save(self, obj):
        if obj.user_story:
            obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions for add/modify this task."))

        if obj.user_story and obj.user_story.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions for add/modify this task."))

        if obj.status and obj.status.project != obj.project:
            raise exc.WrongArguments(_("You don't have permissions for add/modify this task."))

        if obj.milestone and obj.user_story and obj.milestone != obj.user_story.milestone:
            raise exc.WrongArguments(_("You don't have permissions for add/modify this task."))

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        serializer = serializers.TasksBulkSerializer(data=request.DATA)
        if serializer.is_valid():
            data = serializer.data
            project = Project.objects.get(id=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            tasks = services.create_tasks_in_bulk(
                data["bulk_tasks"], milestone_id=data["sprint_id"], user_story_id=data["us_id"],
                status_id=data.get("status_id") or project.default_task_status_id,
                project=project, owner=request.user, callback=self.post_save, precall=self.pre_save)
            tasks_serialized = self.serializer_class(tasks, many=True)

            return response.Ok(tasks_serialized.data)

        return response.BadRequest(serializer.errors)
