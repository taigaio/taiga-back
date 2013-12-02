# -*- coding: utf-8 -*-

import json

from django import http
from greenmine.base import sites


COORS_ALLOWED_ORIGINS = '*'
COORS_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH', 'HEAD']
COORS_ALLOWED_HEADERS = ['content-type', 'x-requested-with',
                         'authorization', 'accept-encoding',
                         'x-disable-pagination', 'x-host']
COORS_ALLOWED_CREDENTIALS = True
COORS_EXPOSE_HEADERS = ["x-pagination-count", "x-paginated", "x-paginated-by",
                        "x-paginated-by", "x-pagination-current", "x-site-host",
                        "x-site-register"]

from .exceptions import format_exception


class CoorsMiddleware(object):
    def _populate_response(self, response):
        response["Access-Control-Allow-Origin"]  = COORS_ALLOWED_ORIGINS
        response["Access-Control-Allow-Methods"] = ",".join(COORS_ALLOWED_METHODS)
        response["Access-Control-Allow-Headers"] = ",".join(COORS_ALLOWED_HEADERS)
        response["Access-Control-Expose-Headers"] = ",".join(COORS_EXPOSE_HEADERS)

        if COORS_ALLOWED_CREDENTIALS:
            response["Access-Control-Allow-Credentials"] = 'true'

    def process_request(self, request):
        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = http.HttpResponse()
            self._populate_response(response)
            return response
        return None

    def process_response(self, request, response):
        self._populate_response(response)
        return response


class SitesMiddleware(object):
    def process_request(self, request):
        domain = request.META.get("HTTP_X_HOST", None)
        if domain is not None:
            try:
                site = sites.get_site_for_domain(domain)
            except sites.SiteNotFound as e:
                detail = format_exception(e)
                return http.HttpResponseBadRequest(json.dumps(detail))
        else:
            site = sites.get_default_site()

        request.site = site
        sites.activate(site)

    def process_response(self, request, response):
        sites.deactivate()

        if hasattr(request, "site"):
            response["X-Site-Host"] = request.site.domain
            response["X-Site-Register"] = "on" if request.site.public_register else "off"

        return response
