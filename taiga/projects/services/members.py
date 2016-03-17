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


def project_has_valid_admins(project, exclude_user=None):
    """
    Checks if the project has any owner membership with a user different than the specified
    """
    admin_memberships = project.memberships.filter(is_admin=True, user__is_active=True)
    if exclude_user:
        admin_memberships = admin_memberships.exclude(user=exclude_user)

    return admin_memberships.count() > 0


def can_user_leave_project(user, project):
    membership = project.memberships.get(user=user)
    if not membership.is_admin:
         return True

    #The user can't leave if is the real owner of the project
    if project.owner == user:
        return False

    if not project_has_valid_admins(project, exclude_user=user):
        return False

    return True


def get_max_memberships_for_project(project):
    """Return tha maximun of membersh for a concrete project.

    :param project: A project object.

    :return: a number or null.
    """
    if project.is_private:
        return project.owner.max_memberships_private_projects
    return project.owner.max_memberships_public_projects


def get_total_project_memberships(project):
    """Return tha total of memberships of a project (members and unaccepted invitations).

    :param project: A project object.

    :return: a number.
    """
    return project.memberships.count()


def check_if_project_privacity_can_be_changed(project):
    """Return if the project privacity can be changed from private to public or viceversa.

    :param project: A project object.

    :return: True if it can be changed or False if can't.
    """
    if project.is_private:
        current_projects = project.owner.owned_projects.filter(is_private=False).count()
        max_projects = project.owner.max_public_projects
        max_memberships = project.owner.max_memberships_public_projects
    else:
        current_projects = project.owner.owned_projects.filter(is_private=True).count()
        max_projects = project.owner.max_private_projects
        max_memberships = project.owner.max_memberships_private_projects

    if max_projects is not None and current_projects >= max_projects:
        return False

    current_memberships = project.memberships.count()

    if max_memberships is not None and current_memberships > max_memberships:
        return False

    return True
