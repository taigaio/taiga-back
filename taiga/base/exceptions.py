# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
Handled exceptions raised by REST framework.

In addition Django's built in 403 and 404 exceptions are handled.
(`django.http.Http404` and `django.core.exceptions.PermissionDenied`)
"""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.http import Http404

from . import response
from . import status

import math


class APIException(Exception):
    """
    Base class for REST framework exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = ""

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Malformed request.")


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Incorrect authentication credentials.")


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Authentication credentials were not provided.")


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You do not have permission to perform this action.")


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _("Method '%s' not allowed.")

    def __init__(self, method, detail=None):
        self.detail = (detail or self.default_detail) % method


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("Could not satisfy the request's Accept header")

    def __init__(self, detail=None, available_renderers=None):
        self.detail = detail or self.default_detail
        self.available_renderers = available_renderers


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = _("Unsupported media type '%s' in request.")

    def __init__(self, media_type, detail=None):
        self.detail = (detail or self.default_detail) % media_type


class Throttled(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Request was throttled.")
    extra_detail = _("Expected available in %d second%s.")

    def __init__(self, wait=None, detail=None):
        if wait is None:
            self.detail = detail or self.default_detail
            self.wait = None
        else:
            format = "%s%s" % ((detail or self.default_detail), self.extra_detail)
            self.detail = format % (wait, wait != 1 and "s" or "")
            self.wait = math.ceil(wait)


class BaseException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unexpected error")

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class NotFound(BaseException, Http404):
    """
    Exception used for not found objects.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Not found.")


class NotSupported(BaseException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _("Method not supported for this endpoint.")


class BadRequest(BaseException):
    """
    Exception used on bad arguments detected
    on api view.
    """
    default_detail = _("Wrong arguments.")


class WrongArguments(BadRequest):
    """
    Exception used on bad arguments detected
    on service. This is same as `BadRequest`.
    """
    default_detail = _("Wrong arguments.")


class RequestValidationError(BadRequest):
    default_detail = _("Data validation error")


class PermissionDenied(PermissionDenied):
    """
    Compatibility subclass of restframework `PermissionDenied`
    exception.
    """
    pass


class IntegrityError(BadRequest):
    default_detail = _("Integrity Error for wrong or invalid arguments")


class PreconditionError(BadRequest):
    """
    Error raised on precondition method on viewset.
    """
    default_detail = _("Precondition error")


class NotAuthenticated(NotAuthenticated):
    """
    Compatibility subclass of restframework `NotAuthenticated`
    exception.
    """
    pass


class Blocked(APIException):
    """
    Exception used on blocked projects
    """
    status_code = status.HTTP_451_BLOCKED
    default_detail = _("Blocked element")


class NotEnoughSlotsForProject(BaseException):
    """
    Exception used on import/edition/creation project errors where the user
    hasn't slots enough
    """
    default_detail = _("No room left for more projects.")

    def __init__(self, is_private, total_memberships, detail=None):
        self.detail = detail or self.default_detail
        self.project_data = {
            "is_private": is_private,
            "total_memberships": total_memberships
        }


def format_exception(exc):
    if isinstance(exc.detail, (dict, list, tuple,)):
        detail = exc.detail
    else:
        class_name = exc.__class__.__name__
        class_module = exc.__class__.__module__
        detail = {
            "_error_message": force_text(exc.detail),
            "_error_type": "{0}.{1}".format(class_module, class_name)
        }

    return detail


def exception_handler(exc):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's builtin `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """

    if isinstance(exc, APIException):
        res = response.Response(format_exception(exc), status=exc.status_code)

        if getattr(exc, "auth_header", None):
            res["WWW-Authenticate"] = exc.auth_header
        if getattr(exc, "wait", None):
            res["X-Throttle-Wait-Seconds"] = "%d" % exc.wait
        if getattr(exc, "project_data", None):
            res["Taiga-Info-Project-Memberships"] = exc.project_data["total_memberships"]
            res["Taiga-Info-Project-Is-Private"] = exc.project_data["is_private"]

        return res

    elif isinstance(exc, Http404):
        return response.NotFound({'_error_message': str(exc)})

    elif isinstance(exc, DjangoPermissionDenied):
        return response.Forbidden({"_error_message": str(exc)})

    # Note: Unhandled exceptions will raise a 500 error.
    return None


ValidationError = DjangoValidationError
