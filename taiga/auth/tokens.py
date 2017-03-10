# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from django.contrib.auth import get_user_model
from taiga.base import exceptions as exc

from django.apps import apps
from django.core import signing
from django.utils.translation import ugettext as _


def get_token_for_user(user, scope):
    """
    Generate a new signed token containing
    a specified user limited for a scope (identified as a string).
    """
    data = {"user_%s_id" % (scope): user.id}
    return signing.dumps(data)


def get_user_for_token(token, scope, max_age=None):
    """
    Given a selfcontained token and a scope try to parse and
    unsign it.

    If max_age is specified it checks token expiration.

    If token passes a validation, returns
    a user instance corresponding with user_id stored
    in the incoming token.
    """
    try:
        data = signing.loads(token, max_age=max_age)
    except signing.BadSignature:
        raise exc.NotAuthenticated(_("Invalid token"))

    model_cls = get_user_model()

    try:
        user = model_cls.objects.get(pk=data["user_%s_id" % (scope)])
    except (model_cls.DoesNotExist, KeyError):
        raise exc.NotAuthenticated(_("Invalid token"))
    else:
        return user
