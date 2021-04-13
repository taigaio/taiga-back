# -*- coding: utf-8 -*-
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
