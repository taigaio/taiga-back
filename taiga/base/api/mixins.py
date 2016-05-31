# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

# The code is partially taken (and modified) from django rest framework
# that is licensed under the following terms:
#
# Copyright (c) 2011-2014, Tom Christie
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import warnings

from django.core.exceptions import ValidationError
from django.http import Http404
from django.db import transaction as tx
from django.utils.translation import ugettext as _

from taiga.base import response

from .settings import api_settings
from .utils import get_object_or_404

from .. import exceptions as exc
from ..decorators import model_pk_lock

def _get_validation_exclusions(obj, pk=None, slug_field=None, lookup_field=None):
    """
    Given a model instance, and an optional pk and slug field,
    return the full list of all other field names on that model.

    For use when performing full_clean on a model instance,
    so we only clean the required fields.
    """
    include = []

    if pk:
        # Pending deprecation
        pk_field = obj._meta.pk
        while pk_field.rel:
            pk_field = pk_field.rel.to._meta.pk
        include.append(pk_field.name)

    if slug_field:
        # Pending deprecation
        include.append(slug_field)

    if lookup_field and lookup_field != 'pk':
        include.append(lookup_field)

    return [field.name for field in obj._meta.fields if field.name not in include]


class CreateModelMixin:
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.check_permissions(request, 'create', serializer.object)

            self.pre_save(serializer.object)
            self.pre_conditions_on_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return response.Created(serializer.data, headers=headers)

        return response.BadRequest(serializer.errors)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}


class ListModelMixin:
    """
    List a queryset.
    """
    empty_error = "Empty list and '%(class_name)s.allow_empty' is False."

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        if not self.allow_empty and not self.object_list:
            warnings.warn('The `allow_empty` parameter is due to be deprecated. '
                          'To use `allow_empty=False` style behavior, You should override '
                          '`get_queryset()` and explicitly raise a 404 on empty querysets.',
                          PendingDeprecationWarning)
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        return response.Ok(serializer.data)


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        self.object = get_object_or_404(self.get_queryset(), **kwargs)

        self.check_permissions(request, 'retrieve', self.object)

        if self.object is None:
            raise Http404

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)


class UpdateModelMixin:
    """
    Update a model instance.
    """

    @tx.atomic
    @model_pk_lock
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        self.object = self.get_object_or_none()
        self.check_permissions(request, 'update', self.object)

        if self.object is None:
            raise Http404

        serializer = self.get_serializer(self.object, data=request.DATA,
                                         files=request.FILES, partial=partial)

        if not serializer.is_valid():
            return response.BadRequest(serializer.errors)

        # Hooks
        try:
            self.pre_save(serializer.object)
            self.pre_conditions_on_save(serializer.object)
        except ValidationError as err:
            # full_clean on model instance may be called in pre_save,
            # so we have to handle eventual errors.
            return response.BadRequest(err.message_dict)

        if self.object is None:
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            return response.Created(serializer.data)

        self.object = serializer.save(force_update=True)
        self.post_save(self.object, created=False)
        return response.Ok(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def pre_save(self, obj):
        """
        Set any attributes on the object that are implicit in the request.
        """
        # pk and/or slug attributes are implicit in the URL.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        slug_field = slug and self.slug_field or None

        if lookup:
            setattr(obj, self.lookup_field, lookup)

        if pk:
            setattr(obj, 'pk', pk)

        if slug:
            setattr(obj, slug_field, slug)

        # Ensure we clean the attributes so that we don't eg return integer
        # pk using a string representation, as provided by the url conf kwarg.
        if hasattr(obj, 'full_clean'):
            exclude = _get_validation_exclusions(obj, pk, slug_field, self.lookup_field)
            obj.full_clean(exclude)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """
    @tx.atomic
    @model_pk_lock
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object_or_none()
        self.check_permissions(request, 'destroy', obj)

        if obj is None:
            raise Http404

        self.pre_delete(obj)
        self.pre_conditions_on_delete(obj)
        obj.delete()
        self.post_delete(obj)
        return response.NoContent()


class BlockeableModelMixin:
    def is_blocked(self, obj):
        raise NotImplementedError("is_blocked must be overridden")

    def pre_conditions_blocked(self, obj):
        #Raises permission exception
        if obj is not None and self.is_blocked(obj):
            raise exc.Blocked(_("Blocked element"))


class BlockeableSaveMixin(BlockeableModelMixin):
    def pre_conditions_on_save(self, obj):
        # Called on create and update calls
        self.pre_conditions_blocked(obj)
        super().pre_conditions_on_save(obj)


class BlockeableDeleteMixin():
    def pre_conditions_on_delete(self, obj):
        # Called on destroy call
        self.pre_conditions_blocked(obj)
        super().pre_conditions_on_delete(obj)


class BlockedByProjectMixin(BlockeableSaveMixin, BlockeableDeleteMixin):
    def is_blocked(self, obj):
        return obj.project is not None and obj.project.blocked_code is not None
