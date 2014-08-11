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
