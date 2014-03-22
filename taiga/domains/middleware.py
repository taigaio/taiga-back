# Copyright 2014 Andrey Antukh <niwi@niwi.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# y ou may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
