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
        queryset = queryset.filter(~Q(id=self.id))

        return self._get_previous_neighbor(queryset), self._get_next_neighbor(queryset)

    def _get_queryset_order_by(self, queryset):
        return queryset.query.order_by or [self._meta.pk.name]

    def _field(self, field):
        return getattr(self, field.lstrip("-"))

    def _filter(self, field, inc, desc):
        if field.startswith("-"):
            field = field[1:]
            operator = desc
        else:
            operator = inc
        return field, operator

    def _or(self, conditions):
        result = Q(**conditions[0])
        for condition in conditions:
            result = result | Q(**condition)
        return result

    def _get_previous_neighbor(self, queryset):
        conds = [{"{}__{}".format(*self._filter(field, "lt", "gt")): self._field(field)}
                 for field in self._get_queryset_order_by(queryset)]
        try:
            return queryset.filter(self._or(conds)).reverse()[0]
        except IndexError:
            return None

    def _get_next_neighbor(self, queryset):
        conds = [{"{}__{}".format(*self._filter(field, "gt", "lt")): self._field(field)}
                 for field in self._get_queryset_order_by(queryset)]
        try:
            return queryset.filter(self._or(conds))[0]
        except IndexError:
            return None
