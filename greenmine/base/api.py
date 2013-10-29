# -*- coding: utf-8 -*-

from django.db import transaction

from reversion.revisions import revision_context_manager
from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response

from .pagination import HeadersPaginationMixin, ConditionalPaginationMixin


class CreateModelMixin(mixins.CreateModelMixin):
    @transaction.atomic
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)


class RetrieveModelMixin(mixins.RetrieveModelMixin):
    @transaction.atomic
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)


class UpdateModelMixin(mixins.UpdateModelMixin):
    @transaction.atomic
    def update(self, *args, **kwargs):
        return super().update(*args, **kwargs)


class ListModelMixin(mixins.ListModelMixin):
    @transaction.atomic
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    Self version of DestroyModelMixin with
    pre_delete hook method.
    """

    def pre_delete(self, obj):
        pass

    @transaction.atomic
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


class ReversionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        revision_context_manager.start()

        try:
            response = super().dispatch(request, *args, **kwargs)
        except Exception as e:
            revision_context_manager.invalidate()
            revision_context_manager.end()
            raise

        if self.request.user.is_authenticated():
            revision_context_manager.set_user(self.request.user)

        if response.status_code > 206:
            revision_context_manager.invalidate()

        revision_context_manager.end()
        return response


class ModelCrudViewSet(DetailAndListSerializersMixin,
                       ReversionMixin,
                       PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       CreateModelMixin,
                       RetrieveModelMixin,
                       UpdateModelMixin,
                       DestroyModelMixin,
                       ListModelMixin,
                       viewsets.GenericViewSet):
    pass


class ModelListViewSet(DetailAndListSerializersMixin,
                       ReversionMixin,
                       PreconditionMixin,
                       HeadersPaginationMixin,
                       ConditionalPaginationMixin,
                       RetrieveModelMixin,
                       ListModelMixin,
                       viewsets.GenericViewSet):
    pass
