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

from django.core.paginator import (
    EmptyPage,
    Page,
    PageNotAnInteger,
    Paginator,
    InvalidPage,
)
from django.http import Http404
from django.http import QueryDict
from django.utils.translation import ugettext as _

from .settings import api_settings

from urllib import parse as urlparse

import warnings


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    query_dict = QueryDict(query).copy()
    query_dict[key] = val
    query = query_dict.urlencode()
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


def strict_positive_int(integer_string, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret <= 0:
        raise ValueError()
    if cutoff:
        ret = min(ret, cutoff)
    return ret


class CustomPage(Page):
    """Handle different number of items on the first page."""

    def start_index(self):
        """Return the 1-based index of the first item on this page."""
        paginator = self.paginator
        # Special case, return zero if no items.
        if paginator.count == 0:
            return 0
        elif self.number == 1:
            return 1
        return (
            (self.number - 2) * paginator.per_page + paginator.first_page + 1)

    def end_index(self):
        """Return the 1-based index of the last item on this page."""
        paginator = self.paginator
        # Special case for the last page because there can be orphans.
        if self.number == paginator.num_pages:
            return paginator.count
        return (self.number - 1) * paginator.per_page + paginator.first_page


class LazyPaginator(Paginator):
    """Implement lazy pagination."""

    def __init__(self, object_list, per_page, **kwargs):
        if 'first_page' in kwargs:
            self.first_page = kwargs.pop('first_page')
        else:
            self.first_page = per_page
        super(LazyPaginator, self).__init__(object_list, per_page, **kwargs)

    def get_current_per_page(self, number):
        return self.first_page if number == 1 else self.per_page

    def validate_number(self, number):
        try:
            number = int(number)
        except ValueError:
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        return number

    def page(self, number):
        number = self.validate_number(number)
        current_per_page = self.get_current_per_page(number)
        if number == 1:
            bottom = 0
        else:
            bottom = ((number - 2) * self.per_page + self.first_page)
        top = bottom + current_per_page
        # Retrieve more objects to check if there is a next page.
        objects = list(self.object_list[bottom:top + self.orphans + 1])
        objects_count = len(objects)
        if objects_count > (current_per_page + self.orphans):
            # If another page is found, increase the total number of pages.
            self._num_pages = number + 1
            # In any case,  return only objects for this page.
            objects = objects[:current_per_page]
        elif (number != 1) and (objects_count <= self.orphans):
            raise EmptyPage('That page contains no results')
        else:
            # This is the last page.
            self._num_pages = number
        return Page(objects, number, self)

    def _get_count(self):
        raise NotImplementedError

    count = property(_get_count)

    def _get_num_pages(self):
        return self._num_pages

    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        raise NotImplementedError

    page_range = property(_get_page_range)


class PaginationMixin(object):
    # Pagination settings
    paginate_by = api_settings.PAGINATE_BY
    paginate_by_param = api_settings.PAGINATE_BY_PARAM
    max_paginate_by = api_settings.MAX_PAGINATE_BY
    page_kwarg = 'page'
    paginator_class = Paginator

    def get_paginate_by(self, queryset=None, **kwargs):
        """
        Return the size of pages to use with pagination.

        If `PAGINATE_BY_PARAM` is set it will attempt to get the page size
        from a named query parameter in the url, eg. ?page_size=100

        Otherwise defaults to using `self.paginate_by`.
        """
        if "HTTP_X_DISABLE_PAGINATION" in self.request.META:
            return None

        if queryset is not None:
            warnings.warn('The `queryset` parameter to `get_paginate_by()` '
                          'is due to be deprecated.',
                          PendingDeprecationWarning, stacklevel=2)

        if self.paginate_by_param:
            try:
                return strict_positive_int(
                    self.request.QUERY_PARAMS[self.paginate_by_param],
                    cutoff=self.max_paginate_by
                )
            except (KeyError, ValueError):
                pass

        return self.paginate_by

    def paginate_queryset(self, queryset, page_size=None):
        """
        Paginate a queryset if required, either returning a page object,
        or `None` if pagination is not configured for this view.
        """
        if "HTTP_X_DISABLE_PAGINATION" in self.request.META:
            return None

        if "HTTP_X_LAZY_PAGINATION" in self.request.META:
            self.paginator_class = LazyPaginator

        deprecated_style = False
        if page_size is not None:
            warnings.warn('The `page_size` parameter to `paginate_queryset()` '
                          'is due to be deprecated. '
                          'Note that the return style of this method is also '
                          'changed, and will simply return a page object '
                          'when called without a `page_size` argument.',
                          PendingDeprecationWarning, stacklevel=2)
            deprecated_style = True
        else:
            # Determine the required page size.
            # If pagination is not configured, simply return None.
            page_size = self.get_paginate_by()
            if not page_size:
                return None

        if not self.allow_empty:
            warnings.warn(
                'The `allow_empty` parameter is due to be deprecated. '
                'To use `allow_empty=False` style behavior, You should override '
                '`get_queryset()` and explicitly raise a 404 on empty querysets.',
                PendingDeprecationWarning, stacklevel=2
            )

        paginator = self.paginator_class(queryset, page_size,
                                         allow_empty_first_page=self.allow_empty)

        page_kwarg = self.kwargs.get(self.page_kwarg)
        page_query_param = self.request.QUERY_PARAMS.get(self.page_kwarg)
        page = page_kwarg or page_query_param or 1
        try:
            page_number = paginator.validate_number(page)
        except InvalidPage:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                                'page_number': page_number,
                                'message': str(e)
            })

        if page is None:
            return page

        if not "HTTP_X_LAZY_PAGINATION" in self.request.META:
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
