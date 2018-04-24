# Copyright (C) 2018 Miguel González <migonzalvar@gmail.com>
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
import datetime as dt

from django.utils import timezone

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField


class DueDateSerializerMixin(serializers.LightSerializer):
    due_date = Field()
    due_date_reason = Field()
    due_date_status = MethodField()

    THRESHOLD = 14

    def get_due_date_status(self, obj):
        if obj.due_date is None:
            return 'not_set'
        elif obj.status and obj.status.is_closed:
            return 'no_longer_applicable'
        elif timezone.now().date() > obj.due_date:
            return 'past_due'
        elif (timezone.now().date() + dt.timedelta(
                days=self.THRESHOLD)) >= obj.due_date:
            return 'due_soon'
        else:
            return 'set'
