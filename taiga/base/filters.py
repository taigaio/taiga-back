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
import operator
from functools import reduce

from django.db.models import Q
from django.db.models.sql.where import ExtraWhere, OR, AND

from rest_framework import filters

from taiga.base import tags

from taiga.projects.models import Membership


class QueryParamsFilterMixin(filters.BaseFilterBackend):
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


class OrderByFilterMixin(QueryParamsFilterMixin):
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

        return super().filter_queryset(request, queryset.order_by(raw_fieldname), view)


class FilterBackend(OrderByFilterMixin):
    """
    Default filter backend.
    """
    pass


class PermissionBasedFilterBackend(FilterBackend):
    permission = None

    def filter_queryset(self, request, queryset, view):
        project_id = None
        if hasattr(view, "filter_fields") and "project" in view.filter_fields:
            project_id = request.QUERY_PARAMS.get("project", None)

        qs = queryset

        if request.user.is_authenticated() and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated():
            memberships_qs = Membership.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)

            # Force users_role table inclusion
            memberships_qs = memberships_qs.exclude(role__slug="not valid slug")
            where_sql  = ["users_role.permissions @> ARRAY['{}']".format(self.permission)]
            memberships_qs = memberships_qs.extra(where=where_sql)

            projects_list = [membership.project_id for membership in memberships_qs]

            if len(projects_list) == 0:
                qs = qs.filter(Q(project__owner=request.user))
            elif len(projects_list) == 1:
                qs = qs.filter(Q(project__owner=request.user) | Q(project=projects_list[0]))
            else:
                qs = qs.filter(Q(project__owner=request.user) | Q(project__in=projects_list))
            extra_where = ExtraWhere(["projects_project.public_permissions @> ARRAY['{}']".format(
                                                                                   self.permission)], [])
            qs.query.where.add(extra_where, OR)
        else:
            qs = qs.exclude(project__owner=-1)
            extra_where = ExtraWhere(["projects_project.anon_permissions @> ARRAY['{}']".format(
                                                                                 self.permission)], [])
            qs.query.where.add(extra_where, AND)

        return super().filter_queryset(request, qs.distinct(), view)


class CanViewProjectFilterBackend(PermissionBasedFilterBackend):
    permission = "view_project"


class CanViewUsFilterBackend(PermissionBasedFilterBackend):
    permission = "view_us"


class CanViewIssuesFilterBackend(PermissionBasedFilterBackend):
    permission = "view_issues"


class CanViewTasksFilterBackend(PermissionBasedFilterBackend):
    permission = "view_tasks"


class CanViewWikiPagesFilterBackend(PermissionBasedFilterBackend):
    permission = "view_wiki_pages"


class CanViewWikiLinksFilterBackend(PermissionBasedFilterBackend):
    permission = "view_wiki_links"


class CanViewMilestonesFilterBackend(PermissionBasedFilterBackend):
    permission = "view_milestones"


class PermissionBasedAttachmentFilterBackend(PermissionBasedFilterBackend):
    permission = None

    def filter_queryset(self, request, queryset, view):
        qs = super().filter_queryset(request, queryset, view)

        ct = view.get_content_type()
        return qs.filter(content_type=ct)


class CanViewUserStoryAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_us"


class CanViewTaskAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_tasks"


class CanViewIssueAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_issues"


class CanViewWikiAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_wiki_pages"


class CanViewProjectObjFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_id = None
        if hasattr(view, "filter_fields") and "project" in view.filter_fields:
            project_id = request.QUERY_PARAMS.get("project", None)

        qs = queryset

        if request.user.is_authenticated() and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated():
            memberships_qs = Membership.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)
            memberships_qs = memberships_qs.exclude(role__slug="not valid slug")  # Force users_role table inclusion
            memberships_qs = memberships_qs.extra(where=["users_role.permissions @> ARRAY['view_project']"])
            projects_list = [membership.project_id for membership in memberships_qs]

            if len(projects_list) == 0:
                qs = qs.filter(Q(owner=request.user))
            elif len(projects_list) == 1:
                qs = qs.filter(Q(owner=request.user) | Q(id=projects_list[0]))
            else:
                qs = qs.filter(Q(owner=request.user) | Q(id__in=projects_list))
            qs.query.where.add(ExtraWhere(["projects_project.public_permissions @> ARRAY['view_project']"], []), OR)
        else:
            qs.query.where.add(ExtraWhere(["projects_project.anon_permissions @> ARRAY['view_project']"], []), AND)

        return super().filter_queryset(request, qs.distinct(), view)


class IsProjectMemberFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated() and request.user.is_superuser:
            queryset = queryset
        elif request.user.is_authenticated():
            queryset = queryset.filter(Q(project__members=request.user) |
                                       Q(project__owner=request.user))
        else:
            queryset = queryset.none()

        return super().filter_queryset(request, queryset.distinct(), view)


class TagsFilter(FilterBackend):
    def __init__(self, filter_name='tags'):
        self.filter_name = filter_name

    def _get_tags_queryparams(self, params):
        return params.get(self.filter_name, "")

    def filter_queryset(self, request, queryset, view):
        query_tags = self._get_tags_queryparams(request.QUERY_PARAMS)
        if query_tags:
            queryset = tags.filter(queryset, contains=query_tags)

        return super().filter_queryset(request, queryset, view)


class QFilter(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        q = request.QUERY_PARAMS.get('q', None)
        if q:
            if q.isdigit():
                qs_args = [Q(ref=q)]
            else:
                qs_args = [Q(subject__icontains=x) for x in q.split()]

            queryset = queryset.filter(reduce(operator.and_, qs_args))

        return queryset
