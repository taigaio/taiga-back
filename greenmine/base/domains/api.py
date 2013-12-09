# -*- coding: utf-8 -*-

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import DomainSerializer


class DomainViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def list(self, request, **kwargs):
        return Response(DomainSerializer(request.domain).data)
