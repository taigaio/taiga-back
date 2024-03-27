# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
