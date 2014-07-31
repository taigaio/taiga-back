from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from . import models


class RoleExistsValidator:
    def validate_role_id(self, attrs, source):
        value = attrs[source]
        if not models.Role.objects.filter(pk=value).exists():
            msg = _("There's no role with that id")
            raise serializers.ValidationError(msg)
        return attrs
