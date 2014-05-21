# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.db import transaction

from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response

from . import pagination
from . import serializers


# Transactional version of rest framework mixins.

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

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class ListModelMixin(mixins.ListModelMixin):
    @transaction.atomic
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


class DestroyModelMixin(mixins.DestroyModelMixin):
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Other mixins (what they are doing here?)

class NeighborsApiMixin(object):
    def filter_queryset(self, queryset, force=False):
        for backend in self.get_filter_backends():
            if force or self.action != "retrieve" or backend not in self.retrieve_exclude_filters:
                queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


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


# Own subclasses of django rest framework viewsets

class ModelCrudViewSet(DetailAndListSerializersMixin,
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
                       PreconditionMixin,
                       pagination.HeadersPaginationMixin,
                       pagination.ConditionalPaginationMixin,
                       RetrieveModelMixin,
                       ListModelMixin,
                       viewsets.GenericViewSet):
    pass


class GenericViewSet(viewsets.GenericViewSet):
    pass
