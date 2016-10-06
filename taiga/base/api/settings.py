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


"""
Settings for REST framework are all namespaced in the REST_FRAMEWORK setting.
For example your project's `settings.py` file might look like this:

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "taiga.base.api.renderers.JSONRenderer",
    )
    "DEFAULT_PARSER_CLASSES": (
        "taiga.base.api.parsers.JSONParser",
    )
}

This module provides the `api_setting` object, that is used to access
REST framework settings, checking for user settings first, then falling
back to the defaults.
"""
from __future__ import unicode_literals

from django.conf import settings
from django.utils import six

import importlib

from . import ISO_8601


USER_SETTINGS = getattr(settings, "REST_FRAMEWORK", None)

DEFAULTS = {
    # Base API policies
    "DEFAULT_RENDERER_CLASSES": (
        "taiga.base.api.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "taiga.base.api.parsers.JSONParser",
        "taiga.base.api.parsers.FormParser",
        "taiga.base.api.parsers.MultiPartParser"
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "taiga.base.api.authentication.SessionAuthentication",
        "taiga.base.api.authentication.BasicAuthentication"
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "taiga.base.api.permissions.AllowAny",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
    ),
    "DEFAULT_CONTENT_NEGOTIATION_CLASS":
        "taiga.base.api.negotiation.DefaultContentNegotiation",

    # Genric view behavior
    "DEFAULT_MODEL_SERIALIZER_CLASS":
        "taiga.base.api.serializers.ModelSerializer",
    "DEFAULT_MODEL_VALIDATOR_CLASS":
        "taiga.base.api.validators.ModelValidator",
    "DEFAULT_FILTER_BACKENDS": (),

    # Throttling
    "DEFAULT_THROTTLE_RATES": {
        "user": None,
        "anon": None,
    },

    # Pagination
    "PAGINATE_BY": None,
    "PAGINATE_BY_PARAM": None,
    "MAX_PAGINATE_BY": None,

    # Authentication
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
    "UNAUTHENTICATED_TOKEN": None,

    # View configuration
    "VIEW_NAME_FUNCTION": "taiga.base.api.views.get_view_name",
    "VIEW_DESCRIPTION_FUNCTION": "taiga.base.api.views.get_view_description",

    # Exception handling
    "EXCEPTION_HANDLER": "taiga.base.api.views.exception_handler",

    # Testing
    "TEST_REQUEST_RENDERER_CLASSES": (
        "taiga.base.api.renderers.MultiPartRenderer",
        "taiga.base.api.renderers.JSONRenderer"
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "multipart",

    # Browser enhancements
    "FORM_METHOD_OVERRIDE": "_method",
    "FORM_CONTENT_OVERRIDE": "_content",
    "FORM_CONTENTTYPE_OVERRIDE": "_content_type",
    "URL_ACCEPT_OVERRIDE": "accept",
    "URL_FORMAT_OVERRIDE": "format",

    "FORMAT_SUFFIX_KWARG": "format",
    "URL_FIELD_NAME": "url",

    # Input and output formats
    "DATE_INPUT_FORMATS": (
        ISO_8601,
    ),
    "DATE_FORMAT": ISO_8601,

    "DATETIME_INPUT_FORMATS": (
        ISO_8601,
    ),
    "DATETIME_FORMAT": None,

    "TIME_INPUT_FORMATS": (
        ISO_8601,
    ),
    "TIME_FORMAT": None,

    # Pending deprecation
    "FILTER_BACKEND": None,
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    "DEFAULT_RENDERER_CLASSES",
    "DEFAULT_PARSER_CLASSES",
    "DEFAULT_AUTHENTICATION_CLASSES",
    "DEFAULT_PERMISSION_CLASSES",
    "DEFAULT_THROTTLE_CLASSES",
    "DEFAULT_CONTENT_NEGOTIATION_CLASS",
    "DEFAULT_MODEL_SERIALIZER_CLASS",
    "DEFAULT_FILTER_BACKENDS",
    "EXCEPTION_HANDLER",
    "FILTER_BACKEND",
    "TEST_REQUEST_RENDERER_CLASSES",
    "UNAUTHENTICATED_USER",
    "UNAUTHENTICATED_TOKEN",
    "VIEW_NAME_FUNCTION",
    "VIEW_DESCRIPTION_FUNCTION"
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class APISettings(object):
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:

        from taiga.base.api.settings import api_settings
        print api_settings.DEFAULT_RENDERER_CLASSES

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.import_strings = import_strings or ()

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        self.validate_setting(attr, val)

        # Cache the result
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if attr == "FILTER_BACKEND" and val is not None:
            # Make sure we can initialize the class
            val()

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
