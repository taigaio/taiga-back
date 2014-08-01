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


class UserStoryStatusExistsValidator:
    def validate_status_id(self, attrs, source):
        value = attrs[source]
        if not models.UserStoryStatus.objects.filter(pk=value).exists():
            msg = _("There's no user story status with that id")
            raise serializers.ValidationError(msg)
        return attrs


class TaskStatusExistsValidator:
    def validate_status_id(self, attrs, source):
        value = attrs[source]
        if not models.TaskStatus.objects.filter(pk=value).exists():
            msg = _("There's no task status with that id")
            raise serializers.ValidationError(msg)
        return attrs
