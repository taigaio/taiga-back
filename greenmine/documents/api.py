# -*- coding: utf-8 -*-

from rest_framework import viewsets

from greenmine.base import filters

from . import serializers
from . import models
from . import permissions


class DocumentsViewSet(viewsets.ModelViewSet):
    model = models.Document
    serializer_class = serializers.DocumentSerializer
    permission_classes = (permissions.DocumentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)

