from django.contrib.auth.models import Group

from greenmine.scrum.models import Project

class RoleGroupsService(object):
    def replicate_role_on_all_projects(self, role):
        for group in role.groups.all():
            self._replicate_role_permissions_on_group(role, group)
        for project in Project.objects.all():
            self._replicate_role_on_project_if_needed(role, project)

    def _replicate_role_permissions_on_group(self, role, group):
        group.permissions.clear()
        for permission in role.permissions.all():
            group.permissions.add(permission)
        group.save()

    def _replicate_role_on_project_if_needed(self, role, project):
        if project.groups.filter(role=role).count() == 0:
            group = Group(name="p%d-r%d" % (project.pk, role.pk), role=role)
            group.save()
            role.groups.add(group)
            self._replicate_role_permissions_on_group(role, group)
