# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from .choices import ADMINS_PERMISSIONS, MEMBERS_PERMISSIONS, ANON_PERMISSIONS

from django.apps import apps


def _get_user_project_membership(user, project, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    if user.is_anonymous:
        return None

    if cache == "user":
        return user.cached_membership_for_project(project)

    return project.cached_memberships_for_user(user)


def _get_object_project(obj):
    project = None
    Project = apps.get_model("projects", "Project")
    if isinstance(obj, Project):
        project = obj
    elif obj and hasattr(obj, 'project'):
        project = obj.project
    return project


def is_project_owner(user, obj):
    project = _get_object_project(obj)
    if project is None:
        return False

    if user.id == project.owner_id:
        return True

    return False


def is_project_admin(user, obj):
    if user.is_superuser:
        return True

    project = _get_object_project(obj)
    if project is None:
        return False

    membership = _get_user_project_membership(user, project)
    if membership and membership.is_admin:
        return True

    return False


def user_has_perm(user, perm, obj=None, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    project = _get_object_project(obj)
    if not project:
        return False

    return perm in get_user_project_permissions(user, project, cache=cache)


def _get_membership_permissions(membership):
    if membership and membership.role and membership.role.permissions:
        return membership.role.permissions
    return []


def calculate_permissions(is_authenticated=False, is_superuser=False, is_member=False,
                          is_admin=False, role_permissions=[], anon_permissions=[],
                          public_permissions=[]):
    if is_superuser:
        admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        public_permissions = []
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    elif is_member:
        if is_admin:
            admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
            members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        else:
            admins_permissions = []
            members_permissions = []
        members_permissions = members_permissions + role_permissions
        public_permissions = public_permissions if public_permissions is not None else []
        anon_permissions = anon_permissions if anon_permissions is not None else []
    elif is_authenticated:
        admins_permissions = []
        members_permissions = []
        public_permissions = public_permissions if public_permissions is not None else []
        anon_permissions = anon_permissions if anon_permissions is not None else []
    else:
        admins_permissions = []
        members_permissions = []
        public_permissions = []
        anon_permissions = anon_permissions if anon_permissions is not None else []

    return set(admins_permissions + members_permissions + public_permissions + anon_permissions)


def get_user_project_permissions(user, project, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    membership = _get_user_project_membership(user, project, cache=cache)
    is_member = membership is not None
    is_admin = is_member and membership.is_admin
    return calculate_permissions(
        is_authenticated = user.is_authenticated,
        is_superuser =  user.is_superuser,
        is_member = is_member,
        is_admin = is_admin,
        role_permissions = _get_membership_permissions(membership),
        anon_permissions = project.anon_permissions,
        public_permissions = project.public_permissions
    )


def set_base_permissions_for_project(project):
    if project.is_private:
        project.anon_permissions = []
        project.public_permissions = []
    else:
        # If a project is public anonymous and registered users should have at
        # least visualization permissions.
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
        project.anon_permissions = list(set((project.anon_permissions or []) + anon_permissions))
        project.public_permissions = list(set((project.public_permissions or []) + anon_permissions))

def is_feedback_owner_and_requestor(feedback, user):
    """
    Checks if the user is allowed to create or modify feedback for a user story
    """
    from taiga.projects.userstories.models import UserStoryFeedback, UserStory

    if feedback is None:
        return False

    user_story_id = feedback.get('user_story')
    if user_story_id:
        try:
            user_story = UserStory.objects.get(id=user_story_id)
        except UserStory.DoesNotExist:
            return False
    
        if user not in user_story.requestors.all():
            return False
    
    feedback_id = feedback.get('id')
    if feedback_id:
        try:
            feedback_obj = UserStoryFeedback.objects.get(id=feedback_id)
        except UserStoryFeedback.DoesNotExist:
            return False
        return feedback_obj.user_id == user.id

    return True

