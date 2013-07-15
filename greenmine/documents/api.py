# -*- coding: utf-8 -*-

from rest_framework import generics

from . import serializers
from . import models
from . import permissions


class DocumentList(generics.ListCreateAPIView):
    model = models.Document
    serializer_class = serializers.DocumentSerializer

    def get_queryset(self):
        return super(DocumentList, self).filter(project__members=self.request.user)


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = models.Document
    serializer_class = serializers.DocumentSerializer
    permission_classes = (permissions.DocumentDetailPermission,)
