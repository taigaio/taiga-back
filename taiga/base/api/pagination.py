# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.utils.translation import ugettext as _

from .settings import api_settings
from .templatetags.api import replace_query_param

import warnings


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
