# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

import json

from django import http
from taiga.base.exceptions import format_exception

from .base import get_domain_for_domain_name
from .base import activate as activate_domain
from .base import deactivate as deactivate_domain
from .base import get_default_domain
from .base import DomainNotFound


class DomainsMiddleware(object):
    """
    Domain middlewate: process request and try resolve domain
    from HTTP_X_HOST header. If no header is specified, one
    default is used.
    """

    def process_request(self, request):
        domain = request.META.get("HTTP_X_HOST", None)
        if domain is not None:
            try:
                domain = get_domain_for_domain_name(domain, follow_alias=True)
            except DomainNotFound as e:
                detail = format_exception(e)
                return http.HttpResponseBadRequest(json.dumps(detail))
        else:
            domain = get_default_domain()

        request.domain = domain
        activate_domain(domain)

    def process_response(self, request, response):
        deactivate_domain()

        if hasattr(request, "domain"):
            response["X-Site-Host"] = request.domain.domain

        return response
