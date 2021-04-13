# -*- coding: utf-8 -*-
from taiga.base import filters


class StorageEntriesFilterBackend(filters.FilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)

        query_params = {}

        if "keys" in request.QUERY_PARAMS:
            field_data = request.QUERY_PARAMS["keys"]
            query_params["key__in"] = field_data.split(",")

        if query_params:
            queryset = queryset.filter(**query_params)

        return queryset
