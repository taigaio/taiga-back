# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import logging

from dateutil.parser import parse as parse_date

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, OuterRef, Subquery
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils.db import to_tsquery

logger = logging.getLogger(__name__)


def get_filter_expression_can_view_projects(user, project_id=None):
    # Filter by user permissions
    if user.is_authenticated and user.is_superuser:
        return Q()
    elif user.is_authenticated:
        # authenticated user & project member
        membership_model = apps.get_model("projects", "Membership")
        memberships_qs = membership_model.objects.filter(user=user)
        if project_id:
            memberships_qs = memberships_qs.filter(project_id=project_id)
        memberships_qs = memberships_qs.filter(
            Q(role__permissions__contains=['view_project']) |
            Q(is_admin=True))

        projects_list = [membership.project_id for membership in
                         memberships_qs]

        return (Q(id__in=projects_list) |
                Q(public_permissions__contains=["view_project"]))
    else:
        # external users / anonymous
        return Q(anon_permissions__contains=["view_project"])


#####################################################################
# Base and Mixins
#####################################################################

class BaseFilterBackend(object):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")


class QueryParamsFilterMixin(BaseFilterBackend):
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
            try:
                queryset = queryset.filter(**query_params)
            except ValueError:
                raise exc.BadRequest(_("Error in filter params types."))

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

        if raw_fieldname in ["owner", "-owner", "assigned_to", "-assigned_to"]:
            raw_fieldname = "{}__full_name".format(raw_fieldname)

        # We need to add a default order if raw_fieldname gives rows with the same value
        return super().filter_queryset(request, queryset.order_by(raw_fieldname, "-id"), view)


class FilterBackend(OrderByFilterMixin):
    """
    Default filter backend.
    """
    pass


class FilterModelAssignedUsers:
    def get_assigned_users_filter(self, model, value):
        assigned_users_ids = model.objects.order_by().filter(
            assigned_users__in=value, id=OuterRef('pk')).values('pk')

        assigned_user_filter = Q(pk__in=Subquery(assigned_users_ids))
        assigned_to_filter = Q(assigned_to__in=value)

        return Q(assigned_user_filter | assigned_to_filter)


#####################################################################
# Permissions filters
#####################################################################

class PermissionBasedFilterBackend(FilterBackend):
    permission = None

    def filter_queryset(self, request, queryset, view):
        project_id = None
        if (hasattr(view, "filter_fields") and "project" in view.filter_fields and
                "project" in request.QUERY_PARAMS):
            try:
                project_id = int(request.QUERY_PARAMS["project"])
            except:
                logger.error("Filtering project diferent value than an integer: {}".format(
                    request.QUERY_PARAMS["project"]
                ))
                raise exc.BadRequest(_("'project' must be an integer value."))

        qs = queryset

        if request.user.is_authenticated and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated:
            membership_model = apps.get_model('projects', 'Membership')
            memberships_qs = membership_model.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)
            memberships_qs = memberships_qs.filter(
                Q(role__permissions__contains=[self.permission]) |
                Q(is_admin=True))

            projects_list = [membership.project_id for membership in memberships_qs]

            qs = qs.filter(Q(project_id__in=projects_list) |
                           Q(project__public_permissions__contains=[self.permission]))
        else:
            qs = qs.filter(project__anon_permissions__contains=[self.permission])

        return super().filter_queryset(request, qs, view)


class CanViewProjectFilterBackend(PermissionBasedFilterBackend):
    permission = "view_project"


class CanViewEpicsFilterBackend(PermissionBasedFilterBackend):
    permission = "view_epics"


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


#####################################################################
# Attachments filters
#####################################################################

class PermissionBasedAttachmentFilterBackend(PermissionBasedFilterBackend):
    permission = None

    def filter_queryset(self, request, queryset, view):
        qs = super().filter_queryset(request, queryset, view)

        ct = view.get_content_type()
        return qs.filter(content_type=ct)


class CanViewEpicAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_epics"


class CanViewUserStoryAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_us"


class CanViewTaskAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_tasks"


class CanViewIssueAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_issues"


class CanViewWikiAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_wiki_pages"


#####################################################################
# User filters
#####################################################################

class MembersFilterBackend(PermissionBasedFilterBackend):
    permission = "view_project"

    def filter_queryset(self, request, queryset, view):
        project_id = None
        project = None
        qs = queryset.filter(is_active=True)
        if "project" in request.QUERY_PARAMS:
            try:
                project_id = int(request.QUERY_PARAMS["project"])
            except:
                logger.error("Filtering project diferent value than an integer: {}".format(
                    request.QUERY_PARAMS["project"]))
                raise exc.BadRequest(_("'project' must be an integer value."))

        if project_id:
            Project = apps.get_model('projects', 'Project')
            project = get_object_or_404(Project, pk=project_id)

        if request.user.is_authenticated and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated:
            Membership = apps.get_model('projects', 'Membership')
            memberships_qs = Membership.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)
            memberships_qs = memberships_qs.filter(
                Q(role__permissions__contains=[self.permission]) |
                Q(is_admin=True))

            projects_list = [membership.project_id for membership in memberships_qs]

            if project:
                is_member = project.id in projects_list
                has_project_public_view_permission = "view_project" in project.public_permissions
                if not is_member and not has_project_public_view_permission:
                    qs = qs.none()

            q = Q(memberships__project_id__in=projects_list) | Q(id=request.user.id)

            # If there is no selected project we want access to users from public projects
            if not project:
                q = q | Q(memberships__project__public_permissions__contains=[self.permission])

            qs = qs.filter(q)

        else:
            if project and "view_project" not in project.anon_permissions:
                qs = qs.none()

            qs = qs.filter(memberships__project__anon_permissions__contains=[self.permission])

        return qs.distinct()


#####################################################################
# Webhooks  filters
#####################################################################

class BaseIsProjectAdminFilterBackend(object):
    def get_project_ids(self, request, view):
        project_id = None
        if hasattr(view, "filter_fields") and "project" in view.filter_fields:
            project_id = request.QUERY_PARAMS.get("project", None)

        if request.user.is_authenticated and request.user.is_superuser:
            return None

        if not request.user.is_authenticated:
            return []

        membership_model = apps.get_model('projects', 'Membership')
        memberships_qs = membership_model.objects.filter(user=request.user, is_admin=True)
        if project_id:
            memberships_qs = memberships_qs.filter(project_id=project_id)

        projects_list = [membership.project_id for membership in memberships_qs]

        return projects_list


class IsProjectAdminFilterBackend(FilterBackend, BaseIsProjectAdminFilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_ids = self.get_project_ids(request, view)
        if project_ids is None:
            queryset = queryset
        elif project_ids == []:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(project_id__in=project_ids)

        return super().filter_queryset(request, queryset, view)


class IsProjectAdminFromWebhookLogFilterBackend(FilterBackend, BaseIsProjectAdminFilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_ids = self.get_project_ids(request, view)
        if project_ids is None:
            queryset = queryset
        elif project_ids == []:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(webhook__project_id__in=project_ids)

        return super().filter_queryset(request, queryset, view)


#####################################################################
# Generic Attributes filters (for User Stories, Tasks and Issues)
#####################################################################

class BaseRelatedFieldsFilter(FilterBackend):
    filter_name = None
    param_name = None
    exclude_param_name = None

    def __init__(self, filter_name=None, param_name=None, exclude_param_name=None):
        if filter_name:
            self.filter_name = filter_name

        if param_name:
            self.param_name = param_name

        if exclude_param_name:
            self.exclude_param_name

    def _prepare_filter_data(self, query_param_value):
        def _transform_value(value):
            try:
                return int(value)
            except:
                if value in self._special_values_dict:
                    return self._special_values_dict[value]
            raise exc.BadRequest()

        values = set([x.strip() for x in query_param_value.split(",")])
        values = map(_transform_value, values)
        return list(values)

    def _get_queryparams(self, params, mode=''):
        param_name = self.exclude_param_name if mode == 'exclude' else \
            self.param_name or self.filter_name
        raw_value = params.get(param_name, None)
        if raw_value:
            value = self._prepare_filter_data(raw_value)
            if None in value:
                qs_in_kwargs = {
                    "{}__in".format(self.filter_name): [v for v in value if v is not None]}
                qs_isnull_kwargs = {"{}__isnull".format(self.filter_name): True}
                return Q(**qs_in_kwargs) | Q(**qs_isnull_kwargs)
            else:
                return Q(**{"{}__in".format(self.filter_name): value})

        return None

    def _prepare_filter_query(self, query):
        return query

    def _prepare_exclude_query(self, query):
        return ~Q(query)

    def filter_queryset(self, request, queryset, view):
        operations = {
            "filter": self._prepare_filter_query,
            "exclude": self._prepare_exclude_query,
        }

        for mode, prepare_method in operations.items():
            query = self._get_queryparams(request.QUERY_PARAMS, mode=mode)
            if query:
                queryset = queryset.filter(prepare_method(query))

        return super().filter_queryset(request, queryset, view)


class OwnersFilter(BaseRelatedFieldsFilter):
    filter_name = 'owner'
    exclude_param_name = 'exclude_owner'


class AssignedToFilter(BaseRelatedFieldsFilter):
    filter_name = 'assigned_to'
    exclude_param_name = 'exclude_assigned_to'


class AssignedUsersFilter(FilterModelAssignedUsers, BaseRelatedFieldsFilter):
    filter_name = 'assigned_users'
    exclude_param_name = 'exclude_assigned_users'

    def filter_user_projects(self, request):
        membership_model = apps.get_model('projects', 'Membership')
        if isinstance(request.user, AnonymousUser):
            return None
        else:
            memberships_project_ids = membership_model.objects.filter(user=request.user).values(
                'project_id')

        return Subquery(memberships_project_ids)

    def filter_queryset(self, request, queryset, view):
        if self.filter_name in request.QUERY_PARAMS or \
                self.exclude_param_name in request.QUERY_PARAMS:
            projects_ids_subquery = self.filter_user_projects(request)
            if projects_ids_subquery:
                queryset = queryset.filter(project_id__in=projects_ids_subquery)

        return super().filter_queryset(request, queryset, view)

    def _get_queryparams(self, params, mode=''):
        param_name = self.exclude_param_name if mode == 'exclude' else self.param_name or \
                                                                       self.filter_name
        raw_value = params.get(param_name, None)
        if raw_value:
            value = self._prepare_filter_data(raw_value)
            UserStoryModel = apps.get_model("userstories", "UserStory")

            if None in value:
                value.remove(None)
                assigned_users_ids = UserStoryModel.objects.order_by().filter(
                    assigned_users__isnull=True,
                    id=OuterRef('pk')).values('pk')

                assigned_user_filter_none = Q(pk__in=Subquery(assigned_users_ids))
                assigned_to_filter_none = Q(assigned_to__isnull=True)

                return (self.get_assigned_users_filter(UserStoryModel, value)
                        | Q(assigned_user_filter_none, assigned_to_filter_none))
            else:
                return self.get_assigned_users_filter(UserStoryModel, value)

        return None


class StatusesFilter(BaseRelatedFieldsFilter):
    filter_name = 'status'
    exclude_param_name = 'exclude_status'


class UserStoryStatusesFilter(StatusesFilter):
    def filter_queryset(self, request, queryset, view):
        project_id = None
        if "project" in request.QUERY_PARAMS:
            try:
                project_id = int(request.QUERY_PARAMS["project"])
            except ValueError:
                logger.error("Filtering project different value tpphan an integer: {}".format(
                    request.QUERY_PARAMS["project"]))
                raise exc.BadRequest(_("'project' must be an integer value."))

        if project_id:
            queryset = queryset.filter(status__project_id=project_id)

        return super().filter_queryset(request, queryset, view)


class IssueTypesFilter(BaseRelatedFieldsFilter):
    filter_name = 'type'
    param_name = 'type'
    exclude_param_name = 'exclude_type'


class PrioritiesFilter(BaseRelatedFieldsFilter):
    filter_name = 'priority'
    exclude_param_name = 'exclude_priority'


class SeveritiesFilter(BaseRelatedFieldsFilter):
    filter_name = 'severity'
    exclude_param_name = 'exclude_severity'


class TagsFilter(FilterBackend):
    filter_name = 'tags'
    exclude_param_name = 'exclude_tags'

    def __init__(self, filter_name=None, exclude_param_name=None):
        if filter_name:
            self.filter_name = filter_name

        if exclude_param_name:
            self.exclude_param_name = exclude_param_name

    def _get_tags_queryparams(self, params, mode=''):
        param_name = self.exclude_param_name if mode == "exclude" else self.filter_name
        tags = params.get(param_name, None)
        if tags:
            return tags.split(",")

        return None

    def _prepare_filter_query(self, tags):
        queries = [Q(tags__contains=[tag]) for tag in tags]
        query = queries.pop()
        for item in queries:
            query |= item

        return Q(query)

    def _prepare_exclude_query(self, tags):
        queries = [Q(tags__contains=[tag]) for tag in tags]
        query = queries.pop()
        for item in queries:
            query |= item

        return ~Q(query)

    def filter_queryset(self, request, queryset, view):
        operations = {
            "filter": self._prepare_filter_query,
            "exclude": self._prepare_exclude_query,
        }

        for mode, prepare_method in operations.items():
            query = self._get_tags_queryparams(request.QUERY_PARAMS, mode=mode)
            if query:
                queryset = queryset.filter(prepare_method(query))

        return super().filter_queryset(request, queryset, view)


class WatchersFilter(FilterBackend):
    filter_name = 'watchers'

    def __init__(self, filter_name=None):
        if filter_name:
            self.filter_name = filter_name

    def _get_watchers_queryparams(self, params):
        watchers = params.get(self.filter_name, None)
        if watchers:
            return watchers.split(",")

        return None

    def filter_queryset(self, request, queryset, view):
        query_watchers = self._get_watchers_queryparams(request.QUERY_PARAMS)
        if query_watchers:
            WatchedModel = apps.get_model("notifications", "Watched")
            watched_type = ContentType.objects.get_for_model(queryset.model)

            try:
                watched_ids = (WatchedModel.objects.filter(content_type=watched_type,
                                                           user__id__in=query_watchers)
                               .values_list("object_id", flat=True))
                queryset = queryset.filter(id__in=watched_ids)
            except ValueError:
                raise exc.BadRequest(_("Error in filter params types."))

        return super().filter_queryset(request, queryset, view)


class BaseCompareFilter(FilterBackend):
    operators = ["", "lt", "gt", "lte", "gte"]

    def __init__(self, filter_name_base=None, operators=None):
        if filter_name_base:
            self.filter_name_base = filter_name_base

    def _get_filter_names(self):
        return [
            self._get_filter_name(operator)
            for operator in self.operators
        ]

    def _get_filter_name(self, operator):
        if operator and len(operator) > 0:
            return "{base}__{operator}".format(
                base=self.filter_name_base, operator=operator
            )
        else:
            return self.filter_name_base

    def _get_constraints(self, params):
        constraints = {}
        for filter_name in self._get_filter_names():
            raw_value = params.get(filter_name, None)
            if raw_value is not None:
                constraints[filter_name] = self._get_value(raw_value)
        return constraints

    def _get_value(self, raw_value):
        return raw_value

    def filter_queryset(self, request, queryset, view):
        constraints = self._get_constraints(request.QUERY_PARAMS)

        if len(constraints) > 0:
            queryset = queryset.filter(**constraints)

        return super().filter_queryset(request, queryset, view)


class BaseDateFilter(BaseCompareFilter):
    def _get_value(self, raw_value):
        return parse_date(raw_value)


class CreatedDateFilter(BaseDateFilter):
    filter_name_base = "created_date"


class ModifiedDateFilter(BaseDateFilter):
    filter_name_base = "modified_date"


class FinishedDateFilter(BaseDateFilter):
    filter_name_base = "finished_date"


class FinishDateFilter(BaseDateFilter):
    filter_name_base = "finish_date"


class EstimatedStartFilter(BaseDateFilter):
    filter_name_base = "estimated_start"


class EstimatedFinishFilter(BaseDateFilter):
    filter_name_base = "estimated_finish"


class MilestoneEstimatedStartFilter(BaseDateFilter):
    filter_name_base = "milestone__estimated_start"


class MilestoneEstimatedFinishFilter(BaseDateFilter):
    filter_name_base = "milestone__estimated_finish"


#####################################################################
# Text search filters
#####################################################################

class QFilter(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        q = request.QUERY_PARAMS.get('q', None)
        if q:
            table = queryset.model._meta.db_table
            where_clause = ("""
                to_tsvector('simple',
                            coalesce({table}.subject, '') || ' ' ||
                            coalesce(array_to_string({table}.tags, ' '), '') || ' ' ||
                            coalesce({table}.ref) || ' ' ||
                            coalesce({table}.description, '')) @@ to_tsquery('simple', %s)
            """.format(table=table))

            queryset = queryset.extra(where=[where_clause], params=[to_tsquery(q)])

        return queryset


class RoleFilter(BaseRelatedFieldsFilter):
    filter_name = "role_id"
    param_name = "role"
    exclude_param_name = "exclude_role"

    def filter_queryset(self, request, queryset, view):
        Membership = apps.get_model('projects', 'Membership')

        operations = {
            "filter": self._prepare_filter_query,
            "exclude": self._prepare_exclude_query,
        }

        for mode, qs_method in operations.items():
            query = self._get_queryparams(request.QUERY_PARAMS, mode=mode)
            if query:
                memberships = Membership.objects.filter(query).exclude(
                    user__isnull=True).values_list("user_id", flat=True)
                if memberships:
                    queryset = queryset.filter(qs_method(Q(assigned_to__in=memberships)))

        return FilterBackend.filter_queryset(self, request, queryset, view)


class UserStoriesRoleFilter(FilterModelAssignedUsers, BaseRelatedFieldsFilter):
    filter_name = "role_id"
    param_name = "role"
    exclude_param_name = 'exclude_role'

    def filter_queryset(self, request, queryset, view):
        Membership = apps.get_model('projects', 'Membership')

        operations = {
            "filter": self._prepare_filter_query,
            "exclude": self._prepare_exclude_query,
        }

        for mode, qs_method in operations.items():
            query = self._get_queryparams(request.QUERY_PARAMS, mode=mode)
            if query:
                memberships = Membership.objects.filter(query).exclude(user__isnull=True). \
                    values_list("user_id", flat=True)
                if memberships:
                    user_story_model = apps.get_model("userstories", "UserStory")
                    queryset = queryset.filter(
                        qs_method(Q(self.get_assigned_users_filter(user_story_model, memberships)))
                    )

        return FilterBackend.filter_queryset(self, request, queryset, view)
