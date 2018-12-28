# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base import filters
from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils.db import get_object_or_none

from taiga.projects.models import Project
from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.notifications.mixins import WatchersViewSetMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.tasks.validators import UpdateMilestoneBulkValidator as \
    TasksUpdateMilestoneValidator
from taiga.projects.issues.validators import UpdateMilestoneBulkValidator as \
    IssuesUpdateMilestoneValidator

from . import serializers
from . import services
from . import validators
from . import models
from . import permissions
from . import utils as milestones_utils

from django_pglocks import advisory_lock
import datetime


class MilestoneViewSet(HistoryResourceMixin, WatchedResourceMixin,
                       BlockedByProjectMixin, ModelCrudViewSet):
    serializer_class = serializers.MilestoneSerializer
    validator_class = validators.MilestoneValidator
    permission_classes = (permissions.MilestonePermission,)
    filter_backends = (
        filters.CanViewMilestonesFilterBackend,
        filters.CreatedDateFilter,
        filters.ModifiedDateFilter,
        filters.EstimatedStartFilter,
        filters.EstimatedFinishFilter,
    )
    filter_fields = (
        "project",
        "project__slug",
        "closed"
    )
    order_by_fields = ("project",
                       "name",
                       "estimated_start",
                       "estimated_finish",
                       "closed",
                       "created_date")
    queryset = models.Milestone.objects.all()

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("milestone-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        res = super().list(request, *args, **kwargs)
        self._add_taiga_info_headers()
        return res

    def _add_taiga_info_headers(self):
        try:
            project_id = int(self.request.QUERY_PARAMS.get("project", None))
            project_model = apps.get_model("projects", "Project")
            project = get_object_or_none(project_model, id=project_id)
        except TypeError:
            project = None

        if project:
            opened_milestones = project.milestones.filter(closed=False).count()
            closed_milestones = project.milestones.filter(closed=True).count()

            self.headers["Taiga-Info-Total-Opened-Milestones"] = opened_milestones
            self.headers["Taiga-Info-Total-Closed-Milestones"] = closed_milestones

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("project", "owner")
        qs = milestones_utils.attach_extra_info(qs, user=self.request.user)
        qs = qs.order_by("-estimated_start")
        return qs

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    @detail_route(methods=['get'])
    def stats(self, request, pk=None):
        milestone = get_object_or_404(models.Milestone, pk=pk)

        self.check_permissions(request, "stats", milestone)

        total_points = milestone.total_points
        milestone_stats = {
            'name': milestone.name,
            'estimated_start': milestone.estimated_start,
            'estimated_finish': milestone.estimated_finish,
            'total_points': total_points,
            'completed_points': milestone.closed_points.values(),
            'total_userstories': milestone.cached_user_stories.count(),
            'completed_userstories': milestone.cached_user_stories.filter(is_closed=True).count(),
            'total_tasks': milestone.tasks.count(),
            'completed_tasks': milestone.tasks.filter(status__is_closed=True).count(),
            'iocaine_doses': milestone.tasks.filter(is_iocaine=True).count(),
            'days': []
        }
        current_date = milestone.estimated_start
        sumTotalPoints = sum(total_points.values())
        optimal_points = sumTotalPoints
        milestone_days = (milestone.estimated_finish - milestone.estimated_start).days
        optimal_points_per_day = sumTotalPoints / milestone_days if milestone_days else 0

        while current_date <= milestone.estimated_finish:
            milestone_stats['days'].append({
                'day': current_date,
                'name': current_date.day,
                'open_points':  sumTotalPoints - milestone.total_closed_points_by_date(current_date),
                'optimal_points': optimal_points,
            })
            current_date = current_date + datetime.timedelta(days=1)
            optimal_points -= optimal_points_per_day

        return response.Ok(milestone_stats)

    @detail_route(methods=["POST"])
    def move_userstories_to_sprint(self, request, pk=None, **kwargs):
        milestone = get_object_or_404(models.Milestone, pk=pk)

        self.check_permissions(request, "move_related_items", milestone)

        validator = validators.UpdateMilestoneBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        milestone_result = get_object_or_404(models.Milestone, pk=data["milestone_id"])

        if data["bulk_stories"]:
            self.check_permissions(request, "move_uss_to_sprint", project)
            services.update_userstories_milestone_in_bulk(data["bulk_stories"], milestone_result)
            services.snapshot_userstories_in_bulk(data["bulk_stories"], request.user)

        return response.NoContent()

    @detail_route(methods=["POST"])
    def move_tasks_to_sprint(self, request, pk=None, **kwargs):
        milestone = get_object_or_404(models.Milestone, pk=pk)

        self.check_permissions(request, "move_related_items", milestone)

        validator = TasksUpdateMilestoneValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        milestone_result = get_object_or_404(models.Milestone, pk=data["milestone_id"])

        if data["bulk_tasks"]:
            self.check_permissions(request, "move_tasks_to_sprint", project)
            services.update_tasks_milestone_in_bulk(data["bulk_tasks"], milestone_result)
            services.snapshot_tasks_in_bulk(data["bulk_tasks"], request.user)

        return response.NoContent()

    @detail_route(methods=["POST"])
    def move_issues_to_sprint(self, request, pk=None, **kwargs):
        milestone = get_object_or_404(models.Milestone, pk=pk)

        self.check_permissions(request, "move_related_items", milestone)

        validator = IssuesUpdateMilestoneValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        milestone_result = get_object_or_404(models.Milestone, pk=data["milestone_id"])

        if data["bulk_issues"]:
            self.check_permissions(request, "move_issues_to_sprint", project)
            services.update_issues_milestone_in_bulk(data["bulk_issues"], milestone_result)
            services.snapshot_issues_in_bulk(data["bulk_issues"], request.user)

        return response.NoContent()


class MilestoneWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.MilestoneWatchersPermission,)
    resource_model = models.Milestone
