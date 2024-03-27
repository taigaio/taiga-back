# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import F
from django.db import transaction as tx

from django.apps import apps
from django.contrib.auth import get_user_model

from django_pglocks import advisory_lock

from .models import Votes, Vote


@tx.atomic
def add_vote(obj, user):
    """Add a vote to an object.

    If the user has already voted the object nothing happends, so this function can be considered
    idempotent.

    :param obj: Any Django model instance.
    :param user: User adding the vote. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    with advisory_lock("vote-{}-{}".format(obj_type.id, obj.id)):
        vote, created = Vote.objects.get_or_create(content_type=obj_type, object_id=obj.id, user=user)
        if not created:
            return

        votes, _ = Votes.objects.get_or_create(content_type=obj_type, object_id=obj.id)
        votes.count = F('count') + 1
        votes.save()
        return vote


@tx.atomic
def remove_vote(obj, user):
    """Remove an user vote from an object.

    If the user has not voted the object nothing happens so this function can be considered
    idempotent.

    :param obj: Any Django model instance.
    :param user: User removing her vote. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    with advisory_lock("vote-{}-{}".format(obj_type.id, obj.id)):
        qs = Vote.objects.filter(content_type=obj_type, object_id=obj.id, user=user)
        if not qs.exists():
            return

    qs.delete()

    votes, _ = Votes.objects.get_or_create(content_type=obj_type, object_id=obj.id)
    votes.count = F('count') - 1
    votes.save()


def get_voters(obj):
    """Get the voters of an object.

    :param obj: Any Django model instance.

    :return: User queryset object representing the users that voted the object.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    return get_user_model().objects.filter(votes__content_type=obj_type, votes__object_id=obj.id)


def get_votes(obj):
    """Get the number of votes an object has.

    :param obj: Any Django model instance.

    :return: Number of votes or `0` if the object has no votes at all.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)

    try:
        return Votes.objects.get(content_type=obj_type, object_id=obj.id).count
    except Votes.DoesNotExist:
        return 0


def get_voted(user_or_id, model):
    """Get the objects voted by an user.

    :param user_or_id: :class:`~taiga.users.models.User` instance or id.
    :param model: Show only objects of this kind. Can be any Django model class.

    :return: Queryset of objects representing the votes of the user.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    conditions = ('votes_vote.content_type_id = %s',
                  '%s.id = votes_vote.object_id' % model._meta.db_table,
                  'votes_vote.user_id = %s')

    if isinstance(user_or_id, get_user_model()):
        user_id = user_or_id.id
    else:
        user_id = user_or_id

    return model.objects.extra(where=conditions, tables=('votes_vote',),
                               params=(obj_type.id, user_id))
