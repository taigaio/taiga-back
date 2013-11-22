# -*- coding: utf-8 -*-

from django.db import transaction

from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework import decorators as rf_decorators
from rest_framework.response import Response

from reversion.revisions import revision_context_manager
from reversion.models import Version
import  reversion


from . import pagination
from . import serializers
from . import decorators

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
    historical_model = Version
    historical_serializer_class = serializers.VersionSerializer
    historical_paginate_by = 5

    def get_historical_queryset(self):
        return reversion.get_unique_for_object(self.get_object())

    def get_historical_serializer_class(self):
        serializer_class = self.historical_serializer_class
        if serializer_class is not None:
            return serializer_class

        assert self.historical_model is not None, \
            "'%s' should either include a 'serializer_class' attribute, " \
            "or use the 'model' attribute as a shortcut for " \
            "automatically generating a serializer class." \
            % self.__class__.__name__

        class DefaultSerializer(self.model_serializer_class):
            class Meta:
                model = self.historical_model
        return DefaultSerializer

    def get_historical_serializer(self, instance=None, data=None, files=None,
                                  many=False, partial=False):
        serializer_class = self.get_historical_serializer_class()
        return serializer_class(instance, data=data, files=files,
                                many=many, partial=partial)

    def get_historical_pagination_serializer(self, page):
        return self.get_historical_serializer(page.object_list, many=True)

    @rf_decorators.link()
    @decorators.change_instance_attr("paginate_by", historical_paginate_by)
    def historical(self, request, *args, **kwargs):
        obj = self.get_object()

        self.historical_object_list = self.get_historical_queryset()

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.historical_object_list)
        if page is not None:
            serializer = self.get_historical_pagination_serializer(page)
        else:
            serializer = self.get_historical_serializer(self.historical_object_list,
                                                        many=True)

        return Response(serializer.data)

    @rf_decorators.action()
    def restore(self, request, vpk=None, *args, **kwargs):
        if not vpk:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            version = reversion.get_for_object(self.get_object()).get(pk=vpk)
            version.revision.revert(delete=True)

            serializer = self.get_serializer(self.get_object())
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED,
                            headers=headers)
        except Version.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                       pagination.HeadersPaginationMixin,
                       pagination.ConditionalPaginationMixin,
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
                       pagination.HeadersPaginationMixin,
                       pagination.ConditionalPaginationMixin,
                       RetrieveModelMixin,
                       ListModelMixin,
                       viewsets.GenericViewSet):
    pass
