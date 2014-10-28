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
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import detail_route
from taiga.base.api import ModelCrudViewSet

from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.history.mixins import HistoryResourceMixin


from . import serializers
from . import models
from . import permissions

import datetime


class MilestoneViewSet(HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    serializer_class = serializers.MilestoneSerializer
    permission_classes = (permissions.MilestonePermission,)
    filter_backends = (filters.CanViewMilestonesFilterBackend,)
    filter_fields = ("project",)

    def get_queryset(self):
        qs = models.Milestone.objects.all()
        qs = qs.prefetch_related("user_stories",
                                 "user_stories__role_points",
                                 "user_stories__role_points__points",
                                 "user_stories__role_points__role")
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
            'total_userstories': milestone.user_stories.count(),
            'completed_userstories': len([us for us in milestone.user_stories.all() if us.is_closed]),
            'total_tasks': milestone.tasks.all().count(),
            'completed_tasks': milestone.tasks.all().filter(status__is_closed=True).count(),
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
                'open_points':  sumTotalPoints - sum(milestone.closed_points_by_date(current_date).values()),
                'optimal_points': optimal_points,
            })
            current_date = current_date + datetime.timedelta(days=1)
            optimal_points -= optimal_points_per_day

        return Response(milestone_stats)
