# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import logging

from django.apps import apps
from django.db.models import Q
from django.utils.translation import gettext as _

from taiga.base import exceptions as exc
from taiga.base.filters import FilterBackend
from taiga.base.filters import get_filter_expression_can_view_projects
from taiga.base.utils.db import to_tsquery

logger = logging.getLogger(__name__)


class DiscoverModeFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        qs = queryset

        if "discover_mode" in request.QUERY_PARAMS:
            field_data = request.QUERY_PARAMS["discover_mode"]
            discover_mode = self._special_values_dict.get(field_data, field_data)

            if discover_mode:
                # discover_mode enabled
                qs = qs.filter(anon_permissions__contains=["view_project"],
                               blocked_code__isnull=True)

                # random order for featured projects
                if request.QUERY_PARAMS.get("is_featured", None) == 'true':
                    qs = qs.order_by("?")

        return super().filter_queryset(request, qs, view)


class CanViewProjectObjFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_id = None

        # Filter by filter_fields
        if (hasattr(view, "filter_fields") and "project" in view.filter_fields and
                "project" in request.QUERY_PARAMS):
            try:
                project_id = int(request.QUERY_PARAMS["project"])
            except:
                logger.error("Filtering project diferent value than an integer: {}".format(
                    request.QUERY_PARAMS["project"]
                ))
                raise exc.BadRequest(_("'project' must be an integer value."))

        filter_expression = get_filter_expression_can_view_projects(
            request.user,
            project_id)

        qs = queryset.filter(filter_expression)

        return super().filter_queryset(request, qs, view)


class QFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        # NOTE: See migtration 0033_text_search_indexes
        q = request.QUERY_PARAMS.get('q', None)
        if q:
            tsquery = "to_tsquery('simple', %s)"
            tsquery_params = [to_tsquery(q)]
            tsvector = """
             setweight(to_tsvector('simple',
                                   coalesce(projects_project.name, '')), 'A') ||
             setweight(to_tsvector('simple',
                                   coalesce(inmutable_array_to_string(projects_project.tags), '')), 'B') ||
             setweight(to_tsvector('simple',
                                   coalesce(projects_project.description, '')), 'C')
            """

            select = {
                "rank": "ts_rank({tsvector},{tsquery})".format(tsquery=tsquery,
                                                               tsvector=tsvector),
            }
            select_params = tsquery_params
            where = ["{tsvector} @@ {tsquery}".format(tsquery=tsquery,
                                                      tsvector=tsvector), ]
            params = tsquery_params
            order_by = ["-rank", ]

            queryset = queryset.extra(select=select,
                                      select_params=select_params,
                                      where=where,
                                      params=params,
                                      order_by=order_by)
        return queryset


class UserOrderFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_anonymous:
            return queryset

        raw_fieldname = request.QUERY_PARAMS.get(self.order_by_query_param, None)
        if not raw_fieldname:
            return queryset

        if raw_fieldname.startswith("-"):
            field_name = raw_fieldname[1:]
        else:
            field_name = raw_fieldname

        if field_name != "user_order":
            return queryset

        model = queryset.model
        sql = """SELECT projects_membership.user_order
                 FROM projects_membership
                 WHERE
                    projects_membership.project_id = {tbl}.id AND
                    projects_membership.user_id = {user_id}
              """

        sql = sql.format(tbl=model._meta.db_table, user_id=request.user.id)
        queryset = queryset.extra(select={"user_order": sql})
        queryset = queryset.order_by(raw_fieldname)
        return queryset
