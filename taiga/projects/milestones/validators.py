from django.utils.translation import ugettext as _

from rest_framework import serializers

from . import models


class SprintExistsValidator:
    def validate_sprint_id(self, attrs, source):
        value = attrs[source]
        if not models.Milestone.objects.filter(pk=value).exists():
            msg = _("There's no sprint with that id")
            raise serializers.ValidationError(msg)
        return attrs
