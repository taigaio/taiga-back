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

from django.db.models import Q

# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from . import monkey
monkey.patch_api_view()
monkey.patch_serializer()
monkey.patch_import_module()
monkey.patch_south_hacks()


class NeighborsMixin:

    def get_neighbors(self, queryset=None):
        """Get the objects around this object.

        :param queryset: A queryset object to use as a starting point. Useful if you need to
        pre-filter the neighbor candidates.

        :return: The tuple `(previous, next)`.
        """
        if queryset is None:
            queryset = type(self).objects.get_queryset()
        queryset = queryset.order_by(*self._get_order_by(queryset))
        queryset = queryset.filter(~Q(id=self.id))

        return self._get_previous_neighbor(queryset), self._get_next_neighbor(queryset)

    def _get_queryset_order_by(self, queryset):
        return queryset.query.order_by

    def _get_order_by(self, queryset):
        return self._get_queryset_order_by(queryset) or self._meta.ordering

    def _get_order_field_value(self, field):
        field = field.lstrip("-")
        obj = self
        for attr in field.split("__"):
            value = getattr(obj, attr, None)
            if value is None:
                break
            obj = value

        return value

    def _transform_order_field_into_lookup(self, field, operator, operator_if_order_desc):
        if field.startswith("-"):
            field = field[1:]
            operator = operator_if_order_desc
        return field, operator

    def _format(self, value):
        if hasattr(value, "format"):
            value = value.format(obj=self)
        return value

    def _or(self, conditions):
        result = Q()
        for condition in conditions:
            result |= Q(**{key: self._format(condition[key]) for key in condition})
        return result

    def _get_neighbor_filters(self, queryset, operator, operator_if_order_desc):
        conds = []
        for field in self._get_queryset_order_by(queryset):
            value = self._get_order_field_value(field)
            if value is None:
                continue
            lookup_field, operator = self._transform_order_field_into_lookup(
                field, operator, operator_if_order_desc)
            lookup = "{}__{}".format(lookup_field, operator)
            conds.append({lookup: value})
        return conds

    def _get_prev_neighbor_filters(self, queryset):
        return self._get_neighbor_filters(queryset, "lte", "gte")

    def _get_next_neighbor_filters(self, queryset):
        return self._get_neighbor_filters(queryset, "gte", "lte")

    def _get_previous_neighbor(self, queryset):
        queryset = queryset.filter(self._or(self._get_prev_neighbor_filters(queryset)))
        try:
            return queryset.reverse()[0]
        except IndexError:
            return None

    def _get_next_neighbor(self, queryset):
        queryset = queryset.filter(self._or(self._get_next_neighbor_filters(queryset)))
        try:
            return queryset[0]
        except IndexError:
            return None
