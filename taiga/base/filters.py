# -*- coding: utf-8 -*-

from django.db.models import Q

from rest_framework import filters


class QueryParamsFilterMixin(object):
    _special_values_dict = {
        'true': True,
        'false': False,
        'null': None,
    }

    def filter_queryset(self, request, queryset, view):
        query_params = {}

        if not hasattr(view, "filter_fields"):
            return queryset

        for field in view.filter_fields:
            if isinstance(field, (tuple, list)):
                param_name, field_name = field
            else:
                param_name, field_name = field, field

            if param_name in request.QUERY_PARAMS:
                field_data = request.QUERY_PARAMS[param_name]
                if field_data in self._special_values_dict:
                    query_params[field_name] = self._special_values_dict[field_data]
                else:
                    query_params[field_name] = field_data

        if query_params:
            queryset = queryset.filter(**query_params)

        return queryset

class OrderByFilterMixin(object):
    order_by_query_param = "order_by"

    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        order_by_fields = getattr(view, "order_by_fields", None)

        raw_fieldname = request.QUERY_PARAMS.get(self.order_by_query_param, None)
        if not raw_fieldname or not order_by_fields:
            return queryset

        if raw_fieldname.startswith("-"):
            field_name = raw_fieldname[1:]
        else:
            field_name = raw_fieldname

        if field_name not in order_by_fields:
            return queryset

        return queryset.order_by(raw_fieldname)


class FilterBackend(OrderByFilterMixin,
                    QueryParamsFilterMixin,
                    filters.BaseFilterBackend):
    """
    Default filter backend.
    """
    pass


class IsProjectMemberFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        user = request.user

        if user.is_authenticated():
            queryset = queryset.filter(Q(project__members=request.user) |
                                       Q(project__owner=request.user))
        return queryset.distinct()
