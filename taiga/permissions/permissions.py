# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Anler Hernández <hello@anler.me>
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
    ('view_us', _('View user stories')),
    ('view_tasks', _('View tasks')),
    ('view_issues', _('View issues')),
    ('view_wiki_pages', _('View wiki pages')),
    ('view_wiki_links', _('View wiki links')),
]

USER_PERMISSIONS = [
    ('view_project', _('View project')),
    ('view_milestones', _('View milestones')),
    ('view_us', _('View user stories')),
    ('view_issues', _('View issues')),
    ('view_tasks', _('View tasks')),
    ('view_wiki_pages', _('View wiki pages')),
    ('view_wiki_links', _('View wiki links')),
    ('request_membership', _('Request membership')),
    ('add_us_to_project', _('Add user story to project')),
    ('add_comments_to_us', _('Add comments to user stories')),
    ('add_comments_to_task', _('Add comments to tasks')),
    ('add_issue', _('Add issues')),
    ('add_comments_to_issue', _('Add comments to issues')),
    ('add_wiki_page', _('Add wiki page')),
    ('modify_wiki_page', _('Modify wiki page')),
    ('add_wiki_link', _('Add wiki link')),
    ('modify_wiki_link', _('Modify wiki link')),
]

MEMBERS_PERMISSIONS = [
    ('view_project', _('View project')),
    # Milestone permissions
    ('view_milestones', _('View milestones')),
    ('add_milestone', _('Add milestone')),
    ('modify_milestone', _('Modify milestone')),
    ('delete_milestone', _('Delete milestone')),
    # US permissions
    ('view_us', _('View user story')),
    ('add_us', _('Add user story')),
    ('modify_us', _('Modify user story')),
    ('delete_us', _('Delete user story')),
    # Task permissions
    ('view_tasks', _('View tasks')),
    ('add_task', _('Add task')),
    ('modify_task', _('Modify task')),
    ('delete_task', _('Delete task')),
    # Issue permissions
    ('view_issues', _('View issues')),
    ('add_issue', _('Add issue')),
    ('modify_issue', _('Modify issue')),
    ('delete_issue', _('Delete issue')),
    # Wiki page permissions
    ('view_wiki_pages', _('View wiki pages')),
    ('add_wiki_page', _('Add wiki page')),
    ('modify_wiki_page', _('Modify wiki page')),
    ('delete_wiki_page', _('Delete wiki page')),
    # Wiki link permissions
    ('view_wiki_links', _('View wiki links')),
    ('add_wiki_link', _('Add wiki link')),
    ('modify_wiki_link', _('Modify wiki link')),
    ('delete_wiki_link', _('Delete wiki link')),
]

OWNERS_PERMISSIONS = [
    ('modify_project', _('Modify project')),
    ('add_member', _('Add member')),
    ('remove_member', _('Remove member')),
    ('delete_project', _('Delete project')),
    ('admin_project_values', _('Admin project values')),
    ('admin_roles', _('Admin roles')),
]
