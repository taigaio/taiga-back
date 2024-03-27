# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

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
