# -*- coding: utf-8 -*-

from rest_framework import viewsets
from rest_framework.response import Response


class SiteViewSet(viewsets.ViewSet):
    def status(self, request, **kwargs):
        return Response({})


sitestatus = SiteViewSet.as_view({"head": "status", "get": "status"})
