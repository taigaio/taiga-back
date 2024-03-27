# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.exceptions import ObjectDoesNotExist

from taiga.base import response
from taiga.base.api import viewsets
from taiga.base.api.utils import get_object_or_error
from taiga.base.decorators import detail_route

from taiga.projects.likes import serializers
from taiga.projects.likes import services


class LikedResourceMixin:
    """
    NOTE:the classes using this mixing must have a method:
    def pre_conditions_on_save(self, obj)
    """
    @detail_route(methods=["POST"])
    def like(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "like", obj)
        self.pre_conditions_on_save(obj)

        services.add_like(obj, user=request.user)
        return response.Ok()

    @detail_route(methods=["POST"])
    def unlike(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "unlike", obj)
        self.pre_conditions_on_save(obj)

        services.remove_like(obj, user=request.user)
        return response.Ok()


class FansViewSetMixin:
    # Is a ModelListViewSet with two required params: permission_classes and resource_model
    serializer_class = serializers.FanSerializer
    list_serializer_class = serializers.FanSerializer
    permission_classes = None
    resource_model = None

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_error(self.resource_model, request.user, pk=resource_id)

        self.check_permissions(request, 'retrieve', resource)

        try:
            self.object = services.get_fans(resource).get(pk=pk)
        except ObjectDoesNotExist: # or User.DoesNotExist
            return response.NotFound()

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def list(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_error(self.resource_model, request.user, pk=resource_id)

        self.check_permissions(request, 'list', resource)

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        resource = self.resource_model.objects.get(pk=self.kwargs.get("resource_id"))
        return services.get_fans(resource)
