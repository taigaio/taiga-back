# -*- coding: utf-8 -*-

import json

from django import http
from taiga.base import domains
from taiga.base.exceptions import format_exception


class DomainsMiddleware(object):
    def process_request(self, request):
        domain = request.META.get("HTTP_X_HOST", None)
        if domain is not None:
            try:
                domain = domains.get_domain_for_domain_name(domain)
            except domains.DomainNotFound as e:
                detail = format_exception(e)
                return http.HttpResponseBadRequest(json.dumps(detail))
        else:
            domain = domains.get_default_domain()

        request.domain = domain
        domains.activate(domain)

    def process_response(self, request, response):
        domains.deactivate()

        if hasattr(request, "domain"):
            response["X-Site-Host"] = request.domain.domain

        return response
