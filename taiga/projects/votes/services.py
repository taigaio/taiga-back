# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db.models import F
from django.db.transaction import atomic
from django.apps import apps
from django.contrib.auth import get_user_model

from .models import Votes, Vote


def add_vote(obj, user):
    """Add a vote to an object.

    If the user has already voted the object nothing happends, so this function can be considered
    idempotent.

    :param obj: Any Django model instance.
    :param user: User adding the vote. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    with atomic():
        vote, created = Vote.objects.get_or_create(content_type=obj_type, object_id=obj.id, user=user)
        if not created:
            return

        votes, _ = Votes.objects.get_or_create(content_type=obj_type, object_id=obj.id)
        votes.count = F('count') + 1
        votes.save()
    return vote


def remove_vote(obj, user):
    """Remove an user vote from an object.

    If the user has not voted the object nothing happens so this function can be considered
    idempotent.

    :param obj: Any Django model instance.
    :param user: User removing her vote. :class:`~taiga.users.models.User` instance.
    """
    obj_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(obj)
    with atomic():
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
