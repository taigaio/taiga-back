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

from ..userstories.serializers import UserStorySerializer
from . import models


class MilestoneSerializer(WatchersValidator, WatchedResourceModelSerializer, serializers.ModelSerializer):
    user_stories = UserStorySerializer(many=True, required=False, read_only=True)
    total_points = serializers.SerializerMethodField("get_total_points")
    closed_points = serializers.SerializerMethodField("get_closed_points")
    client_increment_points = serializers.SerializerMethodField("get_client_increment_points")
    team_increment_points = serializers.SerializerMethodField("get_team_increment_points")

    class Meta:
        model = models.Milestone
        read_only_fields = ("id", "created_date", "modified_date")

    def get_total_points(self, obj):
        return sum(obj.total_points.values())

    def get_closed_points(self, obj):
        return sum(obj.closed_points.values())

    def get_client_increment_points(self, obj):
        return sum(obj.client_increment_points.values())

    def get_team_increment_points(self, obj):
        return sum(obj.team_increment_points.values())

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
