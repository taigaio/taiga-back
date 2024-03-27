# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from functools import partial

from django.utils.translation import gettext as _
from django.conf import settings

from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.api import viewsets
from taiga.base.decorators import list_route
from taiga.projects.services.invitations import accept_invitation_by_existing_user

from . import serializers
from .authentication import AUTH_HEADER_TYPES
from .permissions import AuthPermission
from .services import private_register_for_new_user
from .services import public_register
from .services import make_auth_response_data
from .services import get_auth_plugins
from .throttling import LoginFailRateThrottle, RegisterSuccessRateThrottle


def _validate_data(data:dict, *, cls):
    """
    Generic function for parse and validate user
    data using specified validator on `cls`
    keyword parameter.

    Raises: RequestValidationError exception if
    some errors found when data is validated.
    """

    validator = cls(data=data)
    if not validator.is_valid():
        raise exc.RequestValidationError(validator.errors)
    return validator.object


get_token = partial(_validate_data, cls=serializers.TokenObtainPairSerializer)
refresh_token = partial(_validate_data, cls=serializers.TokenRefreshSerializer)
verify_token = partial(_validate_data, cls=serializers.TokenVerifySerializer)
parse_public_register_data = partial(_validate_data, cls=serializers.PublicRegisterSerializer)
parse_private_register_data = partial(_validate_data, cls=serializers.PrivateRegisterSerializer)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AuthPermission,)
    throttle_classes = (LoginFailRateThrottle, RegisterSuccessRateThrottle)

    serializer_class = None

    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    # Login view: /api/v1/auth
    def create(self, request, **kwargs):
        self.check_permissions(request, 'get_token', None)
        auth_plugins = get_auth_plugins()

        login_type = request.DATA.get("type", "").lower()

        if login_type == "normal":
            # Default login process
            data = get_token(request.DATA)
        elif login_type in auth_plugins:
            data = auth_plugins[login_type]['login_func'](request)
        else:
            raise exc.BadRequest(_("invalid login type"))

        # Processing invitation token
        invitation_token = request.DATA.get("invitation_token", None)
        if invitation_token:
            accept_invitation_by_existing_user(invitation_token, data['id'])

        return response.Ok(data)

    # Refresh token view: /api/v1/auth/refresh
    @list_route(methods=["POST"])
    def refresh(self, request, **kwargs):
        self.check_permissions(request, 'refresh_token', None)
        data = refresh_token(request.DATA)
        return response.Ok(data)

    # Validate token view: /api/v1/auth/verify
    @list_route(methods=["POST"])
    def verify(self, request, **kwargs):
        if not settings.DEBUG:
            return response.Forbidden()

        self.check_permissions(request, 'verify_token', None)
        data = verify_token(request.DATA)
        return response.Ok(data)


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

    # Register user: /api/v1/auth/register
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

