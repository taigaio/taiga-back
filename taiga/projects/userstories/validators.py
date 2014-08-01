from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from . import models


class UserStoryExistsValidator:
    def validate_us_id(self, attrs, source):
        value = attrs[source]
        if not models.UserStory.objects.filter(pk=value).exists():
            msg = _("There's no user story with that id")
            raise serializers.ValidationError(msg)
        return attrs
