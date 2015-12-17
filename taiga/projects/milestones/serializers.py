# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from taiga.base.api import serializers
from taiga.base.utils import json
from taiga.projects.notifications.mixins import WatchedResourceModelSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.votes.utils import attach_total_voters_to_queryset, attach_is_voter_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset, attach_is_watcher_to_queryset

from ..userstories.serializers import UserStoryListSerializer
from . import models


class MilestoneSerializer(WatchersValidator, WatchedResourceModelSerializer, serializers.ModelSerializer):
    user_stories = serializers.SerializerMethodField("get_user_stories")
    total_points = serializers.SerializerMethodField("get_total_points")
    closed_points = serializers.SerializerMethodField("get_closed_points")

    class Meta:
        model = models.Milestone
        read_only_fields = ("id", "created_date", "modified_date")

    def get_user_stories(self, obj):
        qs = obj.user_stories.prefetch_related("role_points",
                                               "role_points__points",
                                               "role_points__role")

        qs = qs.select_related("milestone",
                               "project",
                               "status",
                               "owner",
                               "assigned_to",
                               "generated_from_issue")

        request = self.context.get("request", None)
        requesting_user = request and request.user or None
        if requesting_user and requesting_user.is_authenticated():
            qs = attach_is_voter_to_queryset(requesting_user, qs)
            qs = attach_is_watcher_to_queryset(requesting_user, qs)

        qs = attach_total_voters_to_queryset(qs)
        qs = attach_watchers_to_queryset(qs)

        return UserStoryListSerializer(qs, many=True).data

    def get_total_points(self, obj):
        return sum(obj.total_points.values())

    def get_closed_points(self, obj):
        return sum(obj.closed_points.values())

    def validate_name(self, attrs, source):
        """
        Check the milestone name is not duplicated in the project on creation
        """
        qs = None
        # If the milestone exists:
        if self.object and attrs.get("name", None):
            qs = models.Milestone.objects.filter(project=self.object.project, name=attrs[source]).exclude(pk=self.object.pk)

        if not self.object and attrs.get("project", None) and attrs.get("name", None):
            qs = models.Milestone.objects.filter(project=attrs["project"], name=attrs[source])

        if qs and qs.exists():
              raise serializers.ValidationError(_("Name duplicated for the project"))

        return attrs
