# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
