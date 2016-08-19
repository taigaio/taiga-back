# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from django.utils.translation import ugettext_lazy as _

ANON_PERMISSIONS = [
    ('view_project', _('View project')),
    ('view_milestones', _('View milestones')),
    ('view_epics', _('View epic')),
    ('view_us', _('View user stories')),
    ('view_tasks', _('View tasks')),
    ('view_issues', _('View issues')),
    ('view_wiki_pages', _('View wiki pages')),
    ('view_wiki_links', _('View wiki links')),
]

MEMBERS_PERMISSIONS = [
    ('view_project', _('View project')),
    # Milestone permissions
    ('view_milestones', _('View milestones')),
    ('add_milestone', _('Add milestone')),
    ('modify_milestone', _('Modify milestone')),
    ('delete_milestone', _('Delete milestone')),
    # Epic permissions
    ('view_epics', _('View epic')),
    ('add_epic', _('Add epic')),
    ('modify_epic', _('Modify epic')),
    ('comment_epic', _('Comment epic')),
    ('delete_epic', _('Delete epic')),
    # US permissions
    ('view_us', _('View user story')),
    ('add_us', _('Add user story')),
    ('modify_us', _('Modify user story')),
    ('comment_us', _('Comment user story')),
    ('delete_us', _('Delete user story')),
    # Task permissions
    ('view_tasks', _('View tasks')),
    ('add_task', _('Add task')),
    ('modify_task', _('Modify task')),
    ('comment_task', _('Comment task')),
    ('delete_task', _('Delete task')),
    # Issue permissions
    ('view_issues', _('View issues')),
    ('add_issue', _('Add issue')),
    ('modify_issue', _('Modify issue')),
    ('comment_issue', _('Comment issue')),
    ('delete_issue', _('Delete issue')),
    # Wiki page permissions
    ('view_wiki_pages', _('View wiki pages')),
    ('add_wiki_page', _('Add wiki page')),
    ('modify_wiki_page', _('Modify wiki page')),
    ('comment_wiki_page', _('Comment wiki page')),
    ('delete_wiki_page', _('Delete wiki page')),
    # Wiki link permissions
    ('view_wiki_links', _('View wiki links')),
    ('add_wiki_link', _('Add wiki link')),
    ('modify_wiki_link', _('Modify wiki link')),
    ('delete_wiki_link', _('Delete wiki link')),
]

ADMINS_PERMISSIONS = [
    ('modify_project', _('Modify project')),
    ('delete_project', _('Delete project')),
    ('add_member', _('Add member')),
    ('remove_member', _('Remove member')),
    ('admin_project_values', _('Admin project values')),
    ('admin_roles', _('Admin roles')),
]
