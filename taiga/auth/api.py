from functools import partial
from enum import Enum

from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework import viewsets
from rest_framework import serializers

from taiga.base.decorators import list_route
from taiga.base import exceptions as exc
from taiga.users.services import get_and_validate_user
from taiga.domains.services import is_public_register_enabled_for_domain

from .serializers import PublicRegisterSerializer
from .serializers import PrivateRegisterForExistingUserSerializer
from .serializers import PrivateRegisterForNewUserSerializer

from .services import private_register_for_existing_user
from .services import private_register_for_new_user
from .services import public_register
from .services import make_auth_response_data


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
    permission_classes = (AllowAny,)

    def _public_register(self, request):
        if not is_public_register_enabled_for_domain(request.domain):
            raise exc.BadRequest(_("Public register is disabled for this domain."))

        try:
            data = parse_public_register_data(request.DATA)
            user = public_register(request.domain, **data)
        except exc.IntegrityError as e:
            raise exc.BadRequest(e.detail)

        data = make_auth_response_data(request.domain, user)
        return Response(data, status=status.HTTP_201_CREATED)

    def _private_register(self, request):
        register_type = parse_register_type(request.DATA)

        if register_type is RegisterTypeEnum.existing_user:
            data = parse_private_register_for_existing_user_data(request.DATA)
            user = private_register_for_existing_user(request.domain, **data)
        else:
            data = parse_private_register_for_new_user_data(request.DATA)
            user = private_register_for_new_user(request.domain, **data)

        data = make_auth_response_data(request.domain, user)
        return Response(data, status=status.HTTP_201_CREATED)

    @list_route(methods=["POST"], permission_classes=[AllowAny])
    def register(self, request, **kwargs):
        type = request.DATA.get("type", None)
        if type == "public":
            return self._public_register(request)
        elif type == "private":
            return self._private_register(request)
        raise exc.BadRequest(_("invalid register type"))

    # Login view: /api/v1/auth
    def create(self, request, **kwargs):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        user = get_and_validate_user(username=username, password=password)
        data = make_auth_response_data(request.domain, user)
        return Response(data, status=status.HTTP_200_OK)
