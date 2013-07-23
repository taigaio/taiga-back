# -*- coding: utf-8 -*-

from rest_framework import filters


class SimpleFilterBackend(filters.BaseFilterBackend):
    _special_values_dict = {
        'true': True,
        'false': False,
        'null': None,
    }

    def filter_queryset(self, request, queryset, view):
        query_params = {}

        for field_name in view.filter_fields:
            if field_name in request.QUERY_PARAMS:
                field_data = request.QUERY_PARAMS[field_name]
                if field_data in self._special_values_dict:
                    query_params[field_name] = self._special_values_dict[field_data]
                else:
                    query_params[field_name] = field_data

        if query_params:
            queryset = queryset.filter(**query_params)

        return queryset
