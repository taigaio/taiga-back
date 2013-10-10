# -*- coding: utf-8 -*-

from rest_framework import viewsets
from .pagination import HeadersPaginationMixin, ConditionalPaginationMixin


class ModelCrudViewSet(HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       viewsets.ModelViewSet):
    pass


class ModelListViewSet(HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       viewsets.ReadOnlyModelViewSet):
    pass
