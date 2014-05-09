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

import json

from rest_framework import serializers

from ..userstories.serializers import UserStorySerializer
from . import models



class MilestoneSerializer(serializers.ModelSerializer):
    user_stories = UserStorySerializer(many=True, required=False)
    closed_points = serializers.FloatField(source='closed_points', required=False)
    client_increment_points = serializers.FloatField(source='client_increment_points', required=False)
    team_increment_points = serializers.FloatField(source='team_increment_points', required=False)

    class Meta:
        model = models.Milestone
