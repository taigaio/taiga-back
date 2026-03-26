# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from contextlib import suppress
from operator import itemgetter

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from taiga.events import events
from taiga.projects import models
from taiga.projects.userstories.models import UserStory


def apply_order_updates(base_orders: dict, new_orders: dict, *, remove_equal_original=False):
    """
    `base_orders` must be a dict containing all the elements that can be affected by
    order modifications.
    `new_orders` must be a dict containing the basic order modifications to apply.

    The result will a base_orders with the specified order changes in new_orders
    and the extra calculated ones applied.
    Extra order updates can be needed when moving elements to intermediate positions.
    The elements where no order update is needed will be removed.
    """
    updated_order_ids = set()
    original_orders = {k: v for k, v in base_orders.items()}

    # Remove the elements from new_orders non existint in base_orders
    invalid_keys = new_orders.keys() - base_orders.keys()
    [new_orders.pop(id, None) for id in invalid_keys]

    # We will apply the multiple order changes by the new position order
    sorted_new_orders = [(k, v) for k, v in new_orders.items()]
    sorted_new_orders = sorted(sorted_new_orders, key=lambda e: e[1])

    for new_order in sorted_new_orders:
        old_order = base_orders[new_order[0]]
        new_order = new_order[1]
        for id, order in base_orders.items():
            # When moving forward only the elements contained in the range new_order - old_order
            # positions need to be updated
            moving_backward = new_order <= old_order and order >= new_order and order < old_order
            # When moving backward all the elements from the new_order position need to bee updated
            moving_forward = new_order >= old_order and order >= new_order
            if moving_backward or moving_forward:
                base_orders[id] += 1
                updated_order_ids.add(id)

    # Overwriting the orders specified
    for id, order in new_orders.items():
        if base_orders[id] != order:
            base_orders[id] = order
            updated_order_ids.add(id)

    # Remove not modified elements
    removing_keys = [id for id in base_orders if id not in updated_order_ids]
    [base_orders.pop(id, None) for id in removing_keys]

    # Remove the elements that remains the same
    if remove_equal_original:
        common_keys = base_orders.keys() & original_orders.keys()
        [base_orders.pop(id, None) for id in common_keys if original_orders[id] == base_orders[id]]


def update_projects_order_in_bulk(bulk_data: list, field: str, user):
    """
    Update the order of user projects in the user membership.
    `bulk_data` should be a list of dicts with the following format:

    [{'project_id': <value>, 'order': <value>}, ...]
    """
    memberships_orders = {m.id: getattr(m, field) for m in user.memberships.all()}
    new_memberships_orders = {}

    for membership_data in bulk_data:
        project_id = membership_data["project_id"]
        with suppress(ObjectDoesNotExist):
            membership = user.memberships.get(project_id=project_id)
            new_memberships_orders[membership.id] = membership_data["order"]

    apply_order_updates(memberships_orders, new_memberships_orders)

    from taiga.base.utils import db
    db.update_attr_in_bulk_for_ids(memberships_orders, field, model=models.Membership)


@transaction.atomic
def bulk_update_epic_status_order(project, user, data):
    updates = [models.EpicStatus(id=id, order=order) for id, order in data]
    models.EpicStatus.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_userstory_status_order(project, user, data):
    updates = [models.UserStoryStatus(id=id, order=order) for id, order in data]
    models.UserStoryStatus.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_points_order(project, user, data):
    updates = [models.Points(id=id, order=order) for id, order in data]
    models.Points.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_task_status_order(project, user, data):
    updates = [models.TaskStatus(id=id, order=order) for id, order in data]
    models.TaskStatus.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_issue_status_order(project, user, data):
    updates = [models.IssueStatus(id=id, order=order) for id, order in data]
    models.IssueStatus.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_issue_type_order(project, user, data):
    updates = [models.IssueType(id=id, order=order) for id, order in data]
    models.IssueType.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_priority_order(project, user, data):
    updates = [models.Priority(id=id, order=order) for id, order in data]
    models.Priority.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_severity_order(project, user, data):
    updates = [models.Severity(id=id, order=order) for id, order in data]
    models.Severity.objects.bulk_update(updates, ['order'])


@transaction.atomic
def bulk_update_swimlane_order(project, user, data):
    updates = [models.Swimlane(id=id, order=order) for id, order in data]
    models.Swimlane.objects.bulk_update(updates, ['order'])

    # Send event related to swimlane changes
    swimlane_ids = tuple(map(itemgetter(0), data))
    events.emit_event_for_ids(ids=swimlane_ids,
                              content_type="projects.swimlane",
                              projectid=project.pk)

@transaction.atomic
def update_order_and_swimlane(swimlane_to_be_deleted, move_to_swimlane):

    # first of all, there will be the user stories without swimlane
    uss_without_swimlane = swimlane_to_be_deleted.project.user_stories \
        .filter(swimlane=None).order_by('kanban_order', 'id')
    ordered_uss_ids = list(uss_without_swimlane.values_list('id', flat=True))
    ordered_swimlane_ids = [None] * len(ordered_uss_ids)

    # get the uss paired with its swimlane
    # except the uss in the swimlane to be deleted, which will go to the destination swimlane
    ordered_swimlanes = {}
    for s in swimlane_to_be_deleted.project.swimlanes.order_by('order'):
        s_id = s.id
        if s_id == swimlane_to_be_deleted.id:
            s_id = move_to_swimlane.id

        ordered_swimlanes[s.id] = {
            'ordered_uss': list(s.user_stories.order_by('kanban_order', 'id').values_list('id', flat=True)),
            'swimlane_id': [s_id] * s.user_stories.count()
        }

    # put the uss in the swimlane to be deleted after the uss in the destination swimlane
    ordered_swimlanes[move_to_swimlane.id]['ordered_uss'].extend(
        ordered_swimlanes[swimlane_to_be_deleted.id]['ordered_uss'])
    ordered_swimlanes[move_to_swimlane.id]['swimlane_id'].extend(
        ordered_swimlanes[swimlane_to_be_deleted.id]['swimlane_id'])
    ordered_swimlanes.pop(swimlane_to_be_deleted.id)

    # compose a flat list with the uss ordered
    # and its equivalent with the corresponding swimlanes
    for k, v in ordered_swimlanes.items():
        ordered_uss_ids.extend(v['ordered_uss'])
        ordered_swimlane_ids.extend(v['swimlane_id'])

    # compose a list of tuples with the new order to make a bulk update
    new_indexes = range(0, len(ordered_uss_ids))
    data = list(zip(ordered_swimlane_ids, ordered_uss_ids, new_indexes))

    updates = [
        UserStory(id=uss_id, kanban_order=new_order, swimlane_id=swimlane_id)
        for swimlane_id, uss_id, new_order in data
    ]
    UserStory.objects.bulk_update(updates, ['kanban_order', 'swimlane_id'])
