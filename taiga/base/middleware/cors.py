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

from django import http
from django.conf import settings


COORS_ALLOWED_ORIGINS = "*"
COORS_ALLOWED_METHODS = ["POST", "GET", "OPTIONS", "PUT", "DELETE", "PATCH", "HEAD"]
COORS_ALLOWED_HEADERS = ["content-type", "x-requested-with",
                         "authorization", "accept-encoding",
                         "x-disable-pagination", "x-lazy-pagination",
                         "x-host", "x-session-id", "set-orders"]
COORS_ALLOWED_CREDENTIALS = True
COORS_EXPOSE_HEADERS = ["x-pagination-count", "x-paginated", "x-paginated-by",
                        "x-pagination-current", "x-pagination-next", "x-pagination-prev",
                        "x-site-host", "x-site-register"]

COORS_EXTRA_EXPOSE_HEADERS = getattr(settings, "APP_EXTRA_EXPOSE_HEADERS", [])


class CoorsMiddleware(object):
    def _populate_response(self, response):
        response["Access-Control-Allow-Origin"] = COORS_ALLOWED_ORIGINS
        response["Access-Control-Allow-Methods"] = ",".join(COORS_ALLOWED_METHODS)
        response["Access-Control-Allow-Headers"] = ",".join(COORS_ALLOWED_HEADERS)
        response["Access-Control-Expose-Headers"] = ",".join(COORS_EXPOSE_HEADERS + COORS_EXTRA_EXPOSE_HEADERS)
        response["Access-Control-Max-Age"] = "3600"

        if COORS_ALLOWED_CREDENTIALS:
            response["Access-Control-Allow-Credentials"] = "true"

    def process_request(self, request):
        if "HTTP_ACCESS_CONTROL_REQUEST_METHOD" in request.META:
            response = http.HttpResponse()
            self._populate_response(response)
            return response
        return None

    def process_response(self, request, response):
        self._populate_response(response)
        return response
