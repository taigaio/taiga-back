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
from django.db.models import Prefetch

from taiga.base import filters
from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils.db import get_object_or_none

from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.votes.utils import attach_total_voters_to_queryset, attach_is_voter_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset, attach_is_watcher_to_queryset

from . import serializers
from . import models
from . import permissions

import datetime


class MilestoneViewSet(HistoryResourceMixin, WatchedResourceMixin,
                       BlockedByProjectMixin, ModelCrudViewSet):
    serializer_class = serializers.MilestoneSerializer
    permission_classes = (permissions.MilestonePermission,)
    filter_backends = (filters.CanViewMilestonesFilterBackend,)
    filter_fields = ("project", "closed")
    queryset = models.Milestone.objects.all()

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

        # Userstories prefetching
        UserStory = apps.get_model("userstories", "UserStory")
        us_qs = UserStory.objects.prefetch_related("role_points",
                                                   "role_points__points",
                                                   "role_points__role")

        us_qs = us_qs.select_related("milestone",
                                     "project",
                                     "status",
                                     "owner",
                                     "assigned_to",
                                     "generated_from_issue")

        us_qs = self.attach_watchers_attrs_to_queryset(us_qs)

        if self.request.user.is_authenticated():
            us_qs = attach_is_voter_to_queryset(self.request.user, us_qs)
            us_qs = attach_is_watcher_to_queryset(us_qs, self.request.user)

        qs = qs.prefetch_related(Prefetch("user_stories", queryset=us_qs))

        # Milestones prefetching
        qs = qs.select_related("project", "owner")
        qs = self.attach_watchers_attrs_to_queryset(qs)

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


class MilestoneWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.MilestoneWatchersPermission,)
    resource_model = models.Milestone
