# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from functools import wraps, partial
from django.core.paginator import Paginator


def as_tuple(function=None, *, remove_nulls=False):
    if function is None:
        return partial(as_tuple, remove_nulls=remove_nulls)

    @wraps(function)
    def _decorator(*args, **kwargs):
        return list(function(*args, **kwargs))

    return _decorator


def as_dict(function):
    @wraps(function)
    def _decorator(*args, **kwargs):
        return dict(function(*args, **kwargs))
    return _decorator


def split_by_n(seq:str, n:int):
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]


def iter_queryset(queryset, itersize:int=20):
    """
    Util function for iterate in more efficient way
    all queryset.
    """
    paginator = Paginator(queryset, itersize)
    for page_num in paginator.page_range:
        page = paginator.page(page_num)
        for element in page.object_list:
            yield element
