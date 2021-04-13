# -*- coding: utf-8 -*-
from taiga.base.api import serializers

from . import models

from taiga.projects.settings.utils import get_allowed_sections


class UserProjectSettingsSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField("get_project_name")
    allowed_sections = serializers.SerializerMethodField("get_allowed_sections")

    class Meta:
        model = models.UserProjectSettings
        fields = ('id', 'project', 'project_name', 'homepage', 'allowed_sections')

    def get_project_name(self, obj):
        return obj.project.name

    def get_allowed_sections(self, obj):
        return get_allowed_sections(obj)
