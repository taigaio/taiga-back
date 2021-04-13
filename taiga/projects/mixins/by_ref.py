# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

from taiga.base import response
from taiga.base.decorators import list_route


class ByRefMixin:
    """
    Get an instance by ref.
    """
    @list_route(methods=["GET"])
    def by_ref(self, request):
        if "ref" not in request.QUERY_PARAMS:
            return response.BadRequest(_("ref param is needed"))

        if "project__slug" not in request.QUERY_PARAMS and "project" not in request.QUERY_PARAMS:
            return response.BadRequest(_("project or project__slug param is needed"))

        retrieve_kwargs = {
            "ref": request.QUERY_PARAMS.get("ref", None)
        }
        project_id = request.QUERY_PARAMS.get("project", None)
        if project_id is not None:
            retrieve_kwargs["project_id"] = project_id

        project_slug = request.QUERY_PARAMS.get("project__slug", None)
        if project_slug is not None:
            retrieve_kwargs["project__slug"] = project_slug

        return self.retrieve(request, **retrieve_kwargs)
