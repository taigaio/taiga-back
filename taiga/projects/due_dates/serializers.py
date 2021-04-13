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
