# -*- coding: utf-8 -*-

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

        self.headers["X-Pagination-Total"] = page.paginator.count
        self.headers["X-Paginated"] = "true"

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
