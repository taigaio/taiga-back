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

from functools import partial

from django.utils.translation import ugettext as _
from django.conf import settings

from taiga.base.api import viewsets
from taiga.base.decorators import list_route
from taiga.base import exceptions as exc
from taiga.base import response

from .validators import PublicRegisterValidator
from .validators import PrivateRegisterValidator

from .services import private_register_for_new_user
from .services import public_register
from .services import make_auth_response_data
from .services import get_auth_plugins
from .services import accept_invitation_by_existing_user

from .permissions import AuthPermission
from .throttling import LoginFailRateThrottle, RegisterSuccessRateThrottle


def _parse_data(data:dict, *, cls):
    """
    Generic function for parse user data using
    specified validator on `cls` keyword parameter.

    Raises: RequestValidationError exception if
    some errors found when data is validated.

    Returns the parsed data.
    """

    validator = cls(data=data)
    if not validator.is_valid():
        raise exc.RequestValidationError(validator.errors)
    return validator.data

# Parse public register data
parse_public_register_data = partial(_parse_data, cls=PublicRegisterValidator)

# Parse private register data for new user
parse_private_register_data = partial(_parse_data, cls=PrivateRegisterValidator)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AuthPermission,)
    throttle_classes = (LoginFailRateThrottle, RegisterSuccessRateThrottle)

    def _public_register(self, request):
        if not settings.PUBLIC_REGISTER_ENABLED:
            raise exc.BadRequest(_("Public registration is disabled."))

        try:
            data = parse_public_register_data(request.DATA)
            user = public_register(**data)
        except exc.IntegrityError as e:
            raise exc.BadRequest(e.detail)

        data = make_auth_response_data(user)
        return response.Created(data)

    def _private_register(self, request):
        data = parse_private_register_data(request.DATA)
        user = private_register_for_new_user(**data)

        data = make_auth_response_data(user)
        return response.Created(data)

    @list_route(methods=["POST"])
    def register(self, request, **kwargs):
        accepted_terms = request.DATA.get("accepted_terms", None)
        if accepted_terms in (None, False):
            raise exc.BadRequest(_("You must accept our terms of service and privacy policy"))

        self.check_permissions(request, 'register', None)

        type = request.DATA.get("type", None)
        if type == "public":
            return self._public_register(request)
        elif type == "private":
            return self._private_register(request)
        raise exc.BadRequest(_("invalid registration type"))

    # Login view: /api/v1/auth
    def create(self, request, **kwargs):
        self.check_permissions(request, 'create', None)
        auth_plugins = get_auth_plugins()

        login_type = request.DATA.get("type", None)
        invitation_token = request.DATA.get("invitation_token", None)

        if login_type in auth_plugins:
            data = auth_plugins[login_type]['login_func'](request)
            if invitation_token:
                accept_invitation_by_existing_user(invitation_token, data['id'])
            return response.Ok(data)

        raise exc.BadRequest(_("invalid login type"))
