# -*- coding: utf-8 -*-

from rest_framework import exceptions
from rest_framework import status
from rest_framework.response import Response

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404

from .utils.json import to_json


class BaseException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Unexpected error'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class NotFound(BaseException):
    """
    Exception used for not found objects.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Not found.'


class BadRequest(BaseException):
    """
    Exception used on bad arguments detected
    on api view.
    """
    default_detail = 'Wrong arguments.'


class WrongArguments(BaseException):
    """
    Exception used on bad arguments detected
    on service. This is same as `BadRequest`.
    """
    default_detail = 'Wrong arguments.'


class PermissionDenied(exceptions.PermissionDenied):
    """
    Compatibility subclass of restframework `PermissionDenied`
    exception.
    """
    pass


class PreconditionError(BaseException):
    """
    Error raised on precondition method on viewset.
    """
    default_detail = "Precondition error"


class InternalError(BaseException):
    """
    Exception for internal errors.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal server error"


class NotAuthenticated(exceptions.NotAuthenticated):
    """
    Compatibility subclass of restframework `NotAuthenticated`
    exception.
    """
    pass


def format_exception(exc):
    # TODO: this method need a refactor.
    # TODO: should return in uniform way all exceptions.

    if isinstance(exc.detail, (dict, list, tuple,)):
        detail = exc.detail
    else:
        class_name = exc.__class__.__name__
        class_module = exc.__class__.__module__
        detail = {
            "_error_message": exc.detail,
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

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['X-Throttle-Wait-Seconds'] = '%d' % exc.wait

        detail = format_exception(exc)
        return Response(detail, status=exc.status_code, headers=headers)

    elif isinstance(exc, Http404):
        return Response({'_error_message': 'Not found'},
                        status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, DjangoPermissionDenied):
        return Response({'_error_message': 'Permission denied'},
                        status=status.HTTP_403_FORBIDDEN)

    # Note: Unhandled exceptions will raise a 500 error.
    return None
