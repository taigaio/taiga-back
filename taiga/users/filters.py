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

from taiga.base.filters import PermissionBasedFilterBackend
from taiga.base.utils.db import to_tsquery

from . import services


class ContactsFilterBackend(PermissionBasedFilterBackend):
    def filter_queryset(self, user, request, queryset, view):
        qs = user.contacts_visible_by_user(request.user)

        exclude_project = request.QUERY_PARAMS.get('exclude_project', None)
        if exclude_project:
            qs = qs.exclude(projects__id=exclude_project)

        q = request.QUERY_PARAMS.get('q', None)
        if q:
            table = qs.model._meta.db_table
            where_clause = ("""
                to_tsvector('simple',
                            coalesce({table}.username, '') || ' ' ||
                            coalesce({table}.full_name) || ' ' ||
                            coalesce({table}.email, '')) @@ to_tsquery('simple', %s)
            """.format(table=table))

            qs = qs.extra(where=[where_clause], params=[to_tsquery(q)])

        return qs.distinct()
