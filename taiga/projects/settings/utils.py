# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
