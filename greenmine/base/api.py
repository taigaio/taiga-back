# -*- coding: utf-8 -*-

from rest_framework import (
    mixins,
    viewsets
)


class ModelCrudViewSet(viewsets.ModelViewSet):
    pass


class ModelListViewSet(viewsets.ReadOnlyModelViewSet):
    pass
