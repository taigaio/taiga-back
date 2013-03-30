import time

from django.conf import settings
from django import http
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.utils.importlib import import_module


class GreenmineSessionMiddleware(object):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.META.get(settings.SESSION_HEADER_NAME, None)
        if not session_key:
            session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        request.session = engine.SessionStore(session_key)

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
        except AttributeError:
            pass
        else:
            if accessed:
                patch_vary_headers(response, ('Cookie',))
            if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = cookie_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 500 responses, refs #3881.
                if response.status_code != 500:
                    request.session.save()
                    response.set_cookie(settings.SESSION_COOKIE_NAME,
                                        request.session.session_key,
                                        max_age=max_age,
                                        expires=expires,
                                        domain=settings.SESSION_COOKIE_DOMAIN,
                                        path=settings.SESSION_COOKIE_PATH,
                                        secure=settings.SESSION_COOKIE_SECURE or None,
                                        httponly=settings.SESSION_COOKIE_HTTPONLY or None)
        return response



COORS_ALLOWED_ORIGINS = getattr(settings, 'COORS_ALLOWED_ORIGINS', '*')
COORS_ALLOWED_METHODS = getattr(settings, 'COORS_ALLOWED_METHODS',
                            ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH'])
COORS_ALLOWED_HEADERS = getattr(settings, 'COORS_ALLOWED_HEADERS',
                            ['Content-Type', 'X-Requested-With',
                             'X-Session-Token', 'Accept-Encoding'])
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
