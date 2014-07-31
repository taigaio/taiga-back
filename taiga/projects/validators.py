from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from . import models


class ProjectExistsValidator:
    def validate_project_id(self, attrs, source):
        value = attrs[source]
        if not models.Project.objects.filter(pk=value).exists():
            msg = _("There's no project with that id")
            raise serializers.ValidationError(msg)
        return attrs
