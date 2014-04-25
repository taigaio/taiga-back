# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
