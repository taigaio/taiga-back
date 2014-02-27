# -*- coding: utf-8 -*-
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
        if not self._get_queryset_order_by(queryset):
            queryset = queryset.order_by(*self._get_order_by())
        queryset = queryset.filter(~Q(id=self.id))

        return self._get_previous_neighbor(queryset), self._get_next_neighbor(queryset)

    def _get_queryset_order_by(self, queryset):
        return queryset.query.order_by or []

    def _get_order_by(self):
        return self._meta.ordering

    def _field(self, field):
        return getattr(self, field.lstrip("-"))

    def _filter(self, field, inc, desc):
        if field.startswith("-"):
            field = field[1:]
            operator = desc
        else:
            operator = inc
        return field, operator

    def _format(self, value):
        if hasattr(value, "format"):
            value = value.format(obj=self)
        return value

    def _or(self, conditions):
        condition = conditions[0]
        result = Q(**{key: self._format(condition[key]) for key in condition})
        for condition in conditions[1:]:
            result = result | Q(**{key: self._format(condition[key]) for key in condition})
        return result

    def _get_prev_neighbor_filters(self, queryset):
        conds = [{"{}__{}".format(*self._filter(field, "lt", "gt")): self._field(field)}
                 for field in self._get_queryset_order_by(queryset)]
        return self._or(conds)

    def _get_previous_neighbor(self, queryset):
        try:
            return queryset.filter(self._get_prev_neighbor_filters(queryset)).reverse()[0]
        except IndexError:
            return None

    def _get_next_neighbor_filters(self, queryset):
        conds = [{"{}__{}".format(*self._filter(field, "gt", "lt")): self._field(field)}
                 for field in self._get_queryset_order_by(queryset)]
        return self._or(conds)

    def _get_next_neighbor(self, queryset):
        try:
            return queryset.filter(self._get_next_neighbor_filters(queryset))[0]
        except IndexError:
            return None
