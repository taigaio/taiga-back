# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.utils.translation import ugettext as _

from taiga.base.api import serializers

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
