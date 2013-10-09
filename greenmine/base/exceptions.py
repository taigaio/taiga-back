# -*- coding: utf-8 -*-

from rest_framework import exceptions
from rest_framework import status


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
