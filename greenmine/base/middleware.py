import time

from django.conf import settings
from django import http
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.utils.importlib import import_module

from django.contrib.sessions.middleware import SessionMiddleware


class GreenmineSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.META.get(settings.SESSION_HEADER_NAME, None)
        if not session_key:
            session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        request.session = engine.SessionStore(session_key)



COORS_ALLOWED_ORIGINS = getattr(settings, 'COORS_ALLOWED_ORIGINS', '*')
COORS_ALLOWED_METHODS = getattr(settings, 'COORS_ALLOWED_METHODS',
                            ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH'])
COORS_ALLOWED_HEADERS = getattr(settings, 'COORS_ALLOWED_HEADERS',
                            ['Content-Type', 'X-Requested-With',
                             'X-Session-Token', 'Accept-Encoding',
                             'X-Disable-Pagination'])
COORS_ALLOWED_CREDENTIALS = getattr(settings, 'COORS_ALLOWED_CREDENTIALS',  True)


class CoorsMiddleware(object):
    def _populate_response(self, response):
        response['Access-Control-Allow-Origin']  = COORS_ALLOWED_ORIGINS
        response['Access-Control-Allow-Methods'] = ",".join(COORS_ALLOWED_METHODS)
        response['Access-Control-Allow-Headers'] = ",".join(COORS_ALLOWED_HEADERS)

        if COORS_ALLOWED_CREDENTIALS:
            response['Access-Control-Allow-Credentials'] = 'true'

    def process_request(self, request):
        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = http.HttpResponse()
            self._populate_response(response)
            return response

        return None

    def process_response(self, request, response):
        self._populate_response(response)
        return response
