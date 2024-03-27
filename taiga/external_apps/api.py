# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from . import serializers
from . import validators
from . import models
from . import permissions
from . import services

from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.api import ModelCrudViewSet, ModelRetrieveViewSet
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import list_route, detail_route

from django.utils.translation import gettext_lazy as _


class Application(ModelRetrieveViewSet):
    serializer_class = serializers.ApplicationSerializer
    validator_class = validators.ApplicationValidator
    permission_classes = (permissions.ApplicationPermission,)
    model = models.Application

    @detail_route(methods=["GET"])
    def token(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            raise exc.NotAuthenticated(_("Authentication required"))

        application = get_object_or_404(models.Application, **kwargs)
        self.check_permissions(request, 'token', request.user)
        try:
            application_token = models.ApplicationToken.objects.get(user=request.user, application=application)
            application_token.update_auth_code()
            application_token.state = request.GET.get("state", None)
            application_token.save()

        except models.ApplicationToken.DoesNotExist:
            application_token = models.ApplicationToken(
                user=request.user,
                application=application
            )

        auth_code_data = serializers.ApplicationTokenSerializer(application_token).data
        return response.Ok(auth_code_data)


class ApplicationToken(ModelCrudViewSet):
    serializer_class = serializers.ApplicationTokenSerializer
    validator_class = validators.ApplicationTokenValidator
    permission_classes = (permissions.ApplicationTokenPermission,)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            raise exc.NotAuthenticated(_("Authentication required"))

        queryset = models.ApplicationToken.objects.filter(user=self.request.user)

        application_id = self.request.QUERY_PARAMS.get("application", None)
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        return queryset

    @list_route(methods=["POST"])
    def authorize(self, request, pk=None):
        if self.request.user.is_anonymous:
            raise exc.NotAuthenticated(_("Authentication required"))

        application_id = request.DATA.get("application", None)
        state = request.DATA.get("state", None)
        application_token = services.authorize_token(application_id, request.user, state)

        auth_code_data = serializers.AuthorizationCodeSerializer(application_token).data
        return response.Ok(auth_code_data)

    @list_route(methods=["POST"])
    def validate(self, request, pk=None):
        application_id = request.DATA.get("application", None)
        auth_code = request.DATA.get("auth_code", None)
        state = request.DATA.get("state", None)
        application_token = get_object_or_404(models.ApplicationToken,
                                              application__id=application_id,
                                              auth_code=auth_code,
                                              state=state)

        application_token.generate_token()
        application_token.save()

        access_token_data = serializers.AccessTokenSerializer(application_token).data
        return response.Ok(access_token_data)

    # POST method disabled
    def create(self, *args, **kwargs):
        raise exc.NotSupported()

    # PATCH and PUT methods disabled
    def update(self, *args, **kwargs):
        raise exc.NotSupported()
