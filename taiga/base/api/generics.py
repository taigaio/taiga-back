# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

from . import views
from . import mixins
from . import pagination
from .settings import api_settings
from .utils import get_object_or_error


class GenericAPIView(pagination.PaginationMixin,
                     views.APIView):
    """
    Base class for all other generic views.
    """

    # You'll need to either set these attributes,
    # or override `get_queryset()`/`get_serializer_class()`.
    queryset = None
    serializer_class = None
    validator_class = None

    # This shortcut may be used instead of setting either or both
    # of the `queryset`/`serializer_class` attributes, although using
    # the explicit style is generally preferred.
    model = None

    # If you want to use object lookups other than pk, set this attribute.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = 'pk'
    lookup_url_kwarg = None

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The following attributes may be subject to change,
    # and should be considered private API.
    model_serializer_class = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS
    model_validator_class = api_settings.DEFAULT_MODEL_VALIDATOR_CLASS

    ######################################
    # These are pending deprecation...

    pk_url_kwarg = 'pk'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    allow_empty = True

    def get_extra_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, instance=None, data=None,
                       files=None, many=False, partial=False):
        """
        Return the serializer instance that should be used for deserializing
        input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        context = self.get_extra_context()
        return serializer_class(instance, data=data, files=files,
                                many=many, partial=partial, context=context)

    def get_validator(self, instance=None, data=None,
                      files=None, many=False, partial=False):
        """
        Return the validator instance that should be used for validating the
        input, and for serializing output.
        """
        validator_class = self.get_validator_class()
        context = self.get_extra_context()
        return validator_class(instance, data=data, files=files,
                               many=many, partial=partial, context=context)

    def filter_queryset(self, queryset, filter_backends=None):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        # NOTE TAIGA: Added filter_backends to overwrite the default behavior.

        backends = filter_backends or self.get_filter_backends()
        for backend in backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_filter_backends(self):
        """
        Returns the list of filter backends that this view requires.
        """
        filter_backends = self.filter_backends or []
        if not filter_backends and hasattr(self, 'filter_backend'):
            raise RuntimeError('The `filter_backend` attribute and `FILTER_BACKEND` setting '
                               'are due to be deprecated in favor of a `filter_backends` '
                               'attribute and `DEFAULT_FILTER_BACKENDS` setting, that take '
                               'a *list* of filter backend classes.')
        return filter_backends

    ###########################################################
    # The following methods provide default implementations   #
    # that you may want to override for more complex cases.   #
    ###########################################################

    def get_serializer_class(self):
        if hasattr(self, "action") and self.action == "list" and hasattr(self, "list_serializer_class"):
            return self.list_serializer_class

        serializer_class = self.serializer_class
        if serializer_class is not None:
            return serializer_class

        assert self.model is not None, ("'%s' should either include a 'serializer_class' attribute, "
                                        "or use the 'model' attribute as a shortcut for "
                                        "automatically generating a serializer class." % self.__class__.__name__)

        class DefaultSerializer(self.model_serializer_class):
            class Meta:
                model = self.model
        return DefaultSerializer

    def get_validator_class(self):
        validator_class = self.validator_class
        serializer_class = self.get_serializer_class()

        # Situations where the validator is the rest framework serializer
        if validator_class is None and serializer_class is not None:
            return serializer_class

        if validator_class is not None:
            return validator_class

        class DefaultValidator(self.model_validator_class):
            class Meta:
                model = self.model
        return DefaultValidator

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        if self.queryset is not None:
            return self.queryset._clone()

        if self.model is not None:
            return self.model._default_manager.all()

        raise ImproperlyConfigured(("'%s' must define 'queryset' or 'model'" % self.__class__.__name__))

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        # Determine the base queryset to use.
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            # NOTE: explicit exception for avoid and fix
            # usage of deprecated way of get_object
            raise RuntimeError("DEPRECATED")

        # Perform the lookup filtering.
        # Note that `pk` and `slug` are deprecated styles of lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)

        if lookup is not None:
            filter_kwargs = {self.lookup_field: lookup}
        elif pk is not None and self.lookup_field == 'pk':
            raise RuntimeError(('The `pk_url_kwarg` attribute is due to be deprecated. '
                                'Use the `lookup_field` attribute instead'))
        elif slug is not None and self.lookup_field == 'pk':
            raise RuntimeError(('The `slug_url_kwarg` attribute is due to be deprecated. '
                                'Use the `lookup_field` attribute instead'))
        else:
            raise ImproperlyConfigured(('Expected view %s to be called with a URL keyword argument '
                                        'named "%s". Fix your URL conf, or set the `.lookup_field` '
                                        'attribute on the view correctly.' %
                                        (self.__class__.__name__, self.lookup_field)))

        obj = get_object_or_error(queryset, self.request.user, **filter_kwargs)
        return obj

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            return None

    ###################################################
    # The following are placeholder methods,          #
    # and are intended to be overridden.              #
    #                                                 #
    # The are not called by GenericAPIView directly,  #
    # but are used by the mixin methods.              #
    ###################################################

    def pre_conditions_on_save(self, obj):
        """
        Placeholder method called by mixins before save for check
        some conditions before save.
        """
        pass

    def pre_conditions_on_delete(self, obj):
        """
        Placeholder method called by mixins before delete for check
        some conditions before delete.
        """
        pass

    def pre_save(self, obj):
        """
        Placeholder method for calling before saving an object.

        May be used to set attributes on the object that are implicit
        in either the request, or the url.
        """
        pass

    def post_save(self, obj, created=False):
        """
        Placeholder method for calling after saving an object.
        """
        pass

    def pre_delete(self, obj):
        """
        Placeholder method for calling before deleting an object.
        """
        pass

    def post_delete(self, obj):
        """
        Placeholder method for calling after deleting an object.
        """
        pass


######################################################
# Concrete view classes that provide method handlers #
# by composing the mixin classes with the base view. #
# NOTE: not used by taiga.                           #
######################################################

class CreateAPIView(mixins.CreateModelMixin,
                    GenericAPIView):

    """
    Concrete view for creating a model instance.
    """
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  GenericAPIView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      GenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(mixins.DestroyModelMixin,
                     GenericAPIView):

    """
    Concrete view for deleting a model instance.
    """
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    GenericAPIView):

    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        GenericAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            GenericAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             GenericAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   GenericAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
