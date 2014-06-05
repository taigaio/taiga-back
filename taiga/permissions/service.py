from taiga.projects.models import Membership, Project
from .permissions import OWNERS_PERMISSIONS, MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS


def _get_user_project_membership(user, project):
    if user.is_anonymous():
        return None

    try:
        return Membership.objects.get(user=user, project=project)
    except Membership.DoesNotExist:
        return None

def _get_object_project(obj):
    project = None

    if isinstance(obj, Project):
        project = obj
    elif obj and hasattr(obj, 'project'):
        project = obj.project
    return project


def is_project_owner(user, obj):
    if user.is_superuser:
        return True

    project = _get_object_project(obj)

    if project:
        return project.owner == user
    return False


def user_has_perm(user, perm, obj=None):
    project = _get_object_project(obj)

    if not project:
        return False

    return perm in get_user_project_permissions(user, project)


def role_has_perm(role, perm):
    return perm in role.permissions


def _get_membership_permissions(membership):
    if membership and membership.role and membership.role.permissions:
        return membership.role.permissions
    return []


def get_user_project_permissions(user, project):
    membership = _get_user_project_membership(user, project)
    if user.is_superuser:
        owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
        public_permissions = list(map(lambda perm: perm[0], USER_PERMISSIONS))
        return set(owner_permissions + members_permissions + public_permissions + anon_permissions)
    elif project.owner == user:
        owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        return set(project.anon_permissions + project.public_permissions + members_permissions + owner_permissions)
    elif membership:
        if membership.is_owner:
            owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
            return set(project.anon_permissions + project.public_permissions + _get_membership_permissions(membership) + owner_permissions)
        else:
            return set(project.anon_permissions + project.public_permissions + _get_membership_permissions(membership))
    elif user.is_authenticated():
        return set(project.anon_permissions + project.public_permissions)
    else:
        return set(project.anon_permissions)
