# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import viewsets
from taiga.base.decorators import list_route


class BaseImporterViewSet(viewsets.ViewSet):
    @list_route(methods=["GET"])
    def list_users(self, request, *args, **kwargs):
        raise NotImplementedError

    @list_route(methods=["GET"])
    def list_projects(self, request, *args, **kwargs):
        raise NotImplementedError

    @list_route(methods=["POST"])
    def import_project(self, request, *args, **kwargs):
        raise NotImplementedError

    @list_route(methods=["GET"])
    def auth_url(self, request, *args, **kwargs):
        raise NotImplementedError

    @list_route(methods=["POST"])
    def authorize(self, request, *args, **kwargs):
        raise NotImplementedError
