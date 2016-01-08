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

from django.utils.translation import ugettext_lazy as _

from django_jinja import library


EXTRA_FIELD_VERBOSE_NAMES = {
    "description_diff": _("description"),
    "content_diff": _("content"),
    "blocked_note_diff": _("blocked note"),
    "milestone": _("sprint"),
}


@library.global_function
def verbose_name(obj_class, field_name):
    if field_name in EXTRA_FIELD_VERBOSE_NAMES:
        return EXTRA_FIELD_VERBOSE_NAMES[field_name]

    try:
        return obj_class._meta.get_field(field_name).verbose_name
    except Exception:
        return field_name


@library.global_function
def lists_diff(list1, list2):
    """
    Get the difference of two list and remove None values.

    >>> list1 = ["a", None, "b", "c"]
    >>> list2 = [None, "b", "d", "e"]
    >>> list(filter(None.__ne__, set(list1) - set(list2)))
    ['c', 'a']
    """
    return list(filter(None.__ne__, set(list1) - set(list2)))
