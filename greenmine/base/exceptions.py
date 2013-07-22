# -*- coding: utf-8 -*-

from rest_framework import exceptions
from rest_framework import status


class PermissionDenied(exceptions.PermissionDenied):
    pass


class NotFound(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Not found"

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class BadRequest(exceptions.ParseError):
    default_detail = "Bad request"


__all__ = ["PermissionDenied", "NotFound", "BadRequest"]
