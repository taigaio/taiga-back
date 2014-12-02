from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from . import models


class TaskExistsValidator:
    def validate_task_id(self, attrs, source):
        value = attrs[source]
        if not models.Task.objects.filter(pk=value).exists():
            msg = _("There's no task with that id")
            raise serializers.ValidationError(msg)
        return attrs
