# -*- coding: utf-8 -*-

from django.db import transaction

from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response

from .pagination import HeadersPaginationMixin, ConditionalPaginationMixin


class AtomicMixin(object):
    @transaction.atomic
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @transaction.atomic
    def put(self, *args, **kwargs):
        return super().put(*args, **kwargs)

    @transaction.atomic
    def patch(self, *args, **kwargs):
        return super().patch(*args, **kwargs)


class DestroyModelMixin(object):
    """
    Self version of DestroyModelMixin with
    pre_delete hook method.
    """

    def pre_delete(self, obj):
        pass

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        self.pre_delete(obj)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class DetailAndListSerializersMixin(object):
    """
    Use a diferent serializer class to the list action.
    """
    list_serializer_class = None

    def get_serializer_class(self):
        if self.action == "list" and self.list_serializer_class:
            return self.list_serializer_class
        return super().get_serializer_class()


class ModelCrudViewSet(AtomicMixin,
                       DetailAndListSerializersMixin,
                       PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       DestroyModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    pass


class ModelListViewSet(AtomicMixin,
                       DetailAndListSerializersMixin,
                       PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       viewsets.ReadOnlyModelViewSet):
    pass
