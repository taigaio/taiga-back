# -*- coding: utf-8 -*-

# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from rest_framework.templatetags.rest_framework import replace_query_param


class ConditionalPaginationMixin(object):
    def get_paginate_by(self, *args, **kwargs):
        if "HTTP_X_DISABLE_PAGINATION" in self.request.META:
            return None
        return super().get_paginate_by(*args, **kwargs)


class HeadersPaginationMixin(object):
    def paginate_queryset(self, queryset, page_size=None):
        page = super().paginate_queryset(queryset=queryset, page_size=page_size)

        if page is None:
            return page

        self.headers["x-pagination-count"] = page.paginator.count
        self.headers["x-paginated"] = "true"
        self.headers["x-paginated-by"] = page.paginator.per_page
        self.headers["x-pagination-current"] = page.number

        if page.has_next():
            num = page.next_page_number()
            url = self.request.build_absolute_uri()
            url = replace_query_param(url, "page", num)
            self.headers["X-Pagination-Next"] = url

        if page.has_previous():
            num = page.previous_page_number()
            url = self.request.build_absolute_uri()
            url = replace_query_param(url, "page", num)
            self.headers["X-Pagination-Prev"] = url

        return page

    def get_pagination_serializer(self, page):
        return self.get_serializer(page.object_list, many=True)
