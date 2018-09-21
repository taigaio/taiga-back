# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base.api import serializers
from taiga.permissions.services import is_project_admin, user_has_perm

from . import models

from taiga.projects.settings.choices import Section


class UserProjectSettingsSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField("get_project_name")
    allowed_sections = serializers.SerializerMethodField("get_allowed_sections")

    class Meta:
        model = models.UserProjectSettings
        fields = ('id', 'project', 'project_name', 'homepage', 'allowed_sections')

    def get_project_name(self, obj):
        return obj.project.name

    def get_allowed_sections(self, obj):
        sections = [Section.timeline, Section.search, Section.team]
        active_modules = {'epics': 'view_epics', 'backlog': 'view_us',
                          'kanban': 'view_us', 'wiki': 'view_wiki_pages',
                          'issues': 'view_issues'}

        for key in active_modules:
            module_name = "is_{}_activated".format(key)
            if getattr(obj.project, module_name) and \
                    user_has_perm(obj.user, active_modules[key], obj.project):
                sections.append(getattr(Section, key))

        if obj.project.videoconferences:
            sections.append(Section.meetup)

        if is_project_admin(obj.user, obj.project):
            sections.append(Section.admin)

        return sections
