from taiga.base.utils import db, text

from .. import models

def get_members_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of members.

    :param bulk_data: List of members in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Member` instances.
    """
    members = []
    for data in bulk_data:
        data_copy = data.copy()
        data_copy.update(additional_fields)
        members.append(models.Membership(**data_copy))
    return members


def create_members_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create members from `bulk_data`.

    :param bulk_data: List of dicts `{"project_id": <>, "role_id": <>, "email": <>}`.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Member` instances.
    """
    members = get_members_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(members, callback, precall)
    return members


def remove_user_from_project(user, project):
    models.Membership.objects.get(project=project, user=user).delete()


def project_has_valid_owners(project, exclude_user=None):
    """
    Checks if the project has any owner membership with a user different than the specified
    """
    owner_memberships = project.memberships.filter(is_owner=True, user__is_active=True)
    if exclude_user:
        owner_memberships = owner_memberships.exclude(user=exclude_user)

    return owner_memberships.count() > 0


def can_user_leave_project(user, project):
    membership = project.memberships.get(user=user)
    if not membership.is_owner:
         return True

    if not project_has_valid_owners(project, exclude_user=user):
        return False

    return True
