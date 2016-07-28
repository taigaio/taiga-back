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

from django.http import HttpResponse
from django.utils.translation import ugettext as _

from taiga.base.api.utils import get_object_or_404
from taiga.base import filters, response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.utils import json
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.milestones.models import Milestone
from taiga.projects.models import Project, TaskStatus
from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.tagging.api import TaggedResourceMixin
from taiga.projects.userstories.models import UserStory

from taiga.projects.votes.mixins.viewsets import VotedResourceMixin, VotersViewSetMixin

from . import models
from . import permissions
from . import serializers
from . import services
from . import validators
from . import utils as tasks_utils


class TaskViewSet(OCCResourceMixin, VotedResourceMixin, HistoryResourceMixin,
                  WatchedResourceMixin, TaggedResourceMixin, BlockedByProjectMixin,
                  ModelCrudViewSet):
    validator_class = validators.TaskValidator
    queryset = models.Task.objects.all()
    permission_classes = (permissions.TaskPermission,)
    filter_backends = (filters.CanViewTasksFilterBackend,
                       filters.OwnersFilter,
                       filters.AssignedToFilter,
                       filters.StatusesFilter,
                       filters.TagsFilter,
                       filters.WatchersFilter,
                       filters.QFilter)
    retrieve_exclude_filters = (filters.OwnersFilter,
                                filters.AssignedToFilter,
                                filters.StatusesFilter,
                                filters.TagsFilter,
                                filters.WatchersFilter)
    filter_fields = ["user_story",
                     "milestone",
                     "project",
                     "project__slug",
                     "assigned_to",
                     "status__is_closed"]

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.TaskNeighborsSerializer

        if self.action == "list":
            return serializers.TaskListSerializer

        return serializers.TaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("milestone",
                               "project",
                               "status",
                               "owner",
                               "assigned_to")

        include_attachments = "include_attachments" in self.request.QUERY_PARAMS
        qs = tasks_utils.attach_extra_info(qs, user=self.request.user,
                                           include_attachments=include_attachments)

        return qs

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

    """
    Updating some attributes of the userstory can affect the ordering in the backlog, kanban or taskboard
    These two methods generate a key for the task and can be used to be compared before and after
    saving
    If there is any difference it means an extra ordering update must be done
    """
    def _us_order_key(self, obj):
        return "{}-{}-{}".format(obj.project_id, obj.user_story_id, obj.us_order)

    def _taskboard_order_key(self, obj):
        return "{}-{}-{}-{}".format(obj.project_id, obj.user_story_id, obj.status_id, obj.taskboard_order)

    def pre_save(self, obj):
        if obj.user_story:
            obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user
        else:
            self._old_us_order_key = self._us_order_key(self.get_object())
            self._old_taskboard_order_key = self._taskboard_order_key(self.get_object())

        super().pre_save(obj)

    def _reorder_if_needed(self, obj, old_order_key, order_key, order_attr,
                           project, user_story=None, status=None, milestone=None):
        # Executes the extra ordering if there is a difference in the  ordering keys
        if old_order_key != order_key:
            extra_orders = json.loads(self.request.META.get("HTTP_SET_ORDERS", "{}"))
            data = [{"task_id": obj.id, "order": getattr(obj, order_attr)}]
            for id, order in extra_orders.items():
                data.append({"task_id": int(id), "order": order})

            return services.update_tasks_order_in_bulk(data,
                                                       order_attr,
                                                       project,
                                                       user_story=user_story,
                                                       status=status,
                                                       milestone=milestone)
        return {}

    def post_save(self, obj, created=False):
        if not created:
            # Let's reorder the related stuff after edit the element
            orders_updated = {}
            updated = self._reorder_if_needed(obj,
                                              self._old_us_order_key,
                                              self._us_order_key(obj),
                                              "us_order",
                                              obj.project,
                                              user_story=obj.user_story)
            orders_updated.update(updated)
            updated = self._reorder_if_needed(obj,
                                              self._old_taskboard_order_key,
                                              self._taskboard_order_key(obj),
                                              "taskboard_order",
                                              obj.project,
                                              user_story=obj.user_story,
                                              status=obj.status,
                                              milestone=obj.milestone)
            orders_updated.update(updated)
            self.headers["Taiga-Info-Order-Updated"] = json.dumps(orders_updated)

        super().post_save(obj, created)

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

    @list_route(methods=["GET"])
    def filters_data(self, request, *args, **kwargs):
        project_id = request.QUERY_PARAMS.get("project", None)
        project = get_object_or_404(Project, id=project_id)

        filter_backends = self.get_filter_backends()
        statuses_filter_backends = (f for f in filter_backends if f != filters.StatusesFilter)
        assigned_to_filter_backends = (f for f in filter_backends if f != filters.AssignedToFilter)
        owners_filter_backends = (f for f in filter_backends if f != filters.OwnersFilter)

        queryset = self.get_queryset()
        querysets = {
            "statuses": self.filter_queryset(queryset, filter_backends=statuses_filter_backends),
            "assigned_to": self.filter_queryset(queryset, filter_backends=assigned_to_filter_backends),
            "owners": self.filter_queryset(queryset, filter_backends=owners_filter_backends),
            "tags": self.filter_queryset(queryset)
        }
        return response.Ok(services.get_tasks_filters_data(project, querysets))

    @list_route(methods=["GET"])
    def by_ref(self, request):
        retrieve_kwargs = {
            "ref": request.QUERY_PARAMS.get("ref", None)
        }
        project_id = request.QUERY_PARAMS.get("project", None)
        if project_id is not None:
            retrieve_kwargs["project_id"] = project_id

        project_slug = request.QUERY_PARAMS.get("project__slug", None)
        if project_slug is not None:
            retrieve_kwargs["project__slug"] = project_slug

        return self.retrieve(request, **retrieve_kwargs)

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
        validator = validators.TasksBulkValidator(data=request.DATA)
        if validator.is_valid():
            data = validator.data
            project = Project.objects.get(id=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            if project.blocked_code is not None:
                raise exc.Blocked(_("Blocked element"))

            tasks = services.create_tasks_in_bulk(
                data["bulk_tasks"], milestone_id=data["sprint_id"], user_story_id=data["us_id"],
                status_id=data.get("status_id") or project.default_task_status_id,
                project=project, owner=request.user, callback=self.post_save, precall=self.pre_save)

            tasks = self.get_queryset().filter(id__in=[i.id for i in tasks])
            tasks_serialized = self.get_serializer_class()(tasks, many=True)

            return response.Ok(tasks_serialized.data)

        return response.BadRequest(validator.errors)

    def _bulk_update_order(self, order_field, request, **kwargs):
        validator = validators.UpdateTasksOrderBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])

        self.check_permissions(request, "bulk_update_order", project)
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        user_story = None
        user_story_id = data.get("user_story_id", None)
        if user_story_id is not None:
            user_story = get_object_or_404(UserStory, pk=user_story_id)

        status = None
        status_id = data.get("status_id", None)
        if status_id is not None:
            status = get_object_or_404(TaskStatus, pk=status_id)

        milestone = None
        milestone_id = data.get("milestone_id", None)
        if milestone_id is not None:
            milestone = get_object_or_404(Milestone, pk=milestone_id)

        ret = services.update_tasks_order_in_bulk(data["bulk_tasks"],
                                                  order_field,
                                                  project,
                                                  user_story=user_story,
                                                  status=status,
                                                  milestone=milestone)
        return response.Ok(ret)

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
