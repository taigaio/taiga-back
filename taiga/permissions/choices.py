# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _

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
