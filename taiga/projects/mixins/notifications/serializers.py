# -*- coding: utf-8 -*-

from django.db.models.loading import get_model

from rest_framework import serializers


class WatcherValidationSerializerMixin(object):
    def validate_watchers(self, attrs, source):
        values =  set(attrs.get(source, []))
        if values:
            project = None
            if "project" in attrs and attrs["project"]:
                if self.object and attrs["project"] == self.object.project.id:
                    project = self.object.project
                else:
                    project_model = get_model("projects", "Project")
                    try:
                        project = project_model.objects.get(project__id=attrs["project"])
                    except project_model.DoesNotExist:
                        pass
            elif self.object:
                project = self.object.project

            if len(values) != get_model("projects", "Membership").objects.filter(project=project,
                                                                                 user__in=values).count():
                raise serializers.ValidationError("Error, some watcher user is not a member of the project")
        return attrs
