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
    ('vote_issues', _('Vote issues')),
    ('view_tasks', _('View tasks')),
    ('view_wiki_pages', _('View wiki pages')),
    ('view_wiki_links', _('View wiki links')),
    ('request_membership', _('Request membership')),
    ('add_us_to_project', _('Add user story to project')),
    ('add_comments_to_us', _('Add comments to user stories')),
    ('add_comments_to_task', _('Add comments to tasks')),
    ('add_issue', _('Add issues')),
    ('add_comments_issue', _('Add comments to issues')),
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
    ('vote_issues', _('Vote issues')),
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
