# -*- coding: utf-8 -*-

from rest_framework import viewsets

from .pagination import HeadersPaginationMixin, ConditionalPaginationMixin


class PreconditionMixin(object):
    def pre_conditions_on_save(self, obj):
        pass

    def pre_conditions_on_delete(self, obj):
        pass

    def pre_save(self, obj):
        super().pre_save(obj)
        self.pre_conditions_on_save(obj)

    def pre_delete(self, obj):
        super().pre_delete(obj)
        self.pre_conditions_on_delete(obj)


class ModelCrudViewSet(PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       viewsets.ModelViewSet):
    pass


class ModelListViewSet(PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       viewsets.ReadOnlyModelViewSet):
    pass
