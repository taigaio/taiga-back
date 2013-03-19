# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseForbidden

class PermissionDeniedException(Exception):
    pass

class PermissionMiddleware(object):
    def process_exception(self, request, exception):
        if not isinstance(exception, PermissionDeniedException):
            return None

        return HttpResponseForbidden("Permission denied for %s" % (request.path))
