# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from taiga.permissions.services import is_project_admin, user_has_perm
from taiga.projects.settings.choices import Section


def get_allowed_sections(obj):
    sections = [Section.timeline]
    active_modules = {'epics': 'view_epics', 'backlog': 'view_us',
                      'kanban': 'view_us', 'wiki': 'view_wiki_pages',
                      'issues': 'view_issues'}

    for key in active_modules:
        module_name = "is_{}_activated".format(key)
        if getattr(obj.project, module_name) and \
                user_has_perm(obj.user, active_modules[key], obj.project):
            sections.append(getattr(Section, key))

    return sections
