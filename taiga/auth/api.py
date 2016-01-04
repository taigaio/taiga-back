# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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
from enum import Enum

from django.utils.translation import ugettext as _
from django.conf import settings

from taiga.base.api import serializers
from taiga.base.api import viewsets
from taiga.base.decorators import list_route
from taiga.base import exceptions as exc
from taiga.base import response

from .serializers import PublicRegisterSerializer
from .serializers import PrivateRegisterForExistingUserSerializer
from .serializers import PrivateRegisterForNewUserSerializer

from .services import private_register_for_existing_user
from .services import private_register_for_new_user
from .services import public_register
from .services import make_auth_response_data
from .services import get_auth_plugins

from .permissions import AuthPermission


def _parse_data(data:dict, *, cls):
    """
    Generic function for parse user data using
    specified serializer on `cls` keyword parameter.

    Raises: RequestValidationError exception if
    some errors found when data is validated.

    Returns the parsed data.
    """

    serializer = cls(data=data)
    if not serializer.is_valid():
        raise exc.RequestValidationError(serializer.errors)
    return serializer.data

# Parse public register data
parse_public_register_data = partial(_parse_data, cls=PublicRegisterSerializer)

# Parse private register data for existing user
parse_private_register_for_existing_user_data = \
    partial(_parse_data, cls=PrivateRegisterForExistingUserSerializer)

# Parse private register data for new user
parse_private_register_for_new_user_data = \
    partial(_parse_data, cls=PrivateRegisterForNewUserSerializer)


class RegisterTypeEnum(Enum):
    new_user = 1
    existing_user = 2


def parse_register_type(userdata:dict) -> str:
    """
    Parses user data and detects that register type is.
    It returns RegisterTypeEnum value.
    """
    # Create adhoc inner serializer for avoid parse
    # manually the user data.
    class _serializer(serializers.Serializer):
        existing = serializers.BooleanField()

    instance = _serializer(data=userdata)
    if not instance.is_valid():
        raise exc.RequestValidationError(instance.errors)

    if instance.data["existing"]:
        return RegisterTypeEnum.existing_user
    return RegisterTypeEnum.new_user


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AuthPermission,)

    def _public_register(self, request):
        if not settings.PUBLIC_REGISTER_ENABLED:
            raise exc.BadRequest(_("Public register is disabled."))

        try:
            data = parse_public_register_data(request.DATA)
            user = public_register(**data)
        except exc.IntegrityError as e:
            raise exc.BadRequest(e.detail)

        data = make_auth_response_data(user)
        return response.Created(data)

    def _private_register(self, request):
        register_type = parse_register_type(request.DATA)

        if register_type is RegisterTypeEnum.existing_user:
            data = parse_private_register_for_existing_user_data(request.DATA)
            user = private_register_for_existing_user(**data)
        else:
            data = parse_private_register_for_new_user_data(request.DATA)
            user = private_register_for_new_user(**data)

        data = make_auth_response_data(user)
        return response.Created(data)

    @list_route(methods=["POST"])
    def register(self, request, **kwargs):
        self.check_permissions(request, 'register', None)

        type = request.DATA.get("type", None)
        if type == "public":
            return self._public_register(request)
        elif type == "private":
            return self._private_register(request)
        raise exc.BadRequest(_("invalid register type"))

    # Login view: /api/v1/auth
    def create(self, request, **kwargs):
        self.check_permissions(request, 'create', None)
        auth_plugins = get_auth_plugins()

        login_type = request.DATA.get("type", None)

        if login_type in auth_plugins:
            data = auth_plugins[login_type]['login_func'](request)
            return response.Ok(data)

        raise exc.BadRequest(_("invalid login type"))
