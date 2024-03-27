# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, OuterRef, Subquery
from django.utils.translation import gettext as _

from taiga.base import filters


def get_assigned_users_filter(model, value):
    assigned_users_ids = model.objects.order_by().filter(
        assigned_users__in=value, id=OuterRef('pk')).values('pk')

    assigned_user_filter = Q(pk__in=Subquery(assigned_users_ids))
    assigned_to_filter = Q(assigned_to__in=value)

    return Q(assigned_user_filter | assigned_to_filter)


class EpicFilter(filters.BaseRelatedFieldsFilter):
    filter_name = "epics"
    param_name = "epic"
    exclude_param_name = 'exclude_epic'


class SwimlanesFilter(filters.BaseRelatedFieldsFilter):
    filter_name = 'swimlane'
    param_name = "swimnlane"
    exclude_param_name = 'exclude_swimlane'


class UserStoryStatusesFilter(filters.StatusesFilter):
    def filter_queryset(self, request, queryset, view):
        project_id = None
        if "project" in request.QUERY_PARAMS:
            try:
                project_id = int(request.QUERY_PARAMS["project"])
            except ValueError:
                logger.error("Filtering user stories by status. Project value should be an integer: {}".format(
                    request.QUERY_PARAMS["project"]))
                raise exc.BadRequest(_("'project' must be an integer value."))

        if project_id:
            queryset = queryset.filter(status__project_id=project_id)

        return super().filter_queryset(request, queryset, view)


class AssignedUsersFilter(filters.BaseRelatedFieldsFilter):
    filter_name = 'assigned_users'
    exclude_param_name = 'exclude_assigned_users'

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

                return (get_assigned_users_filter(UserStoryModel, value)
                        | Q(assigned_user_filter_none, assigned_to_filter_none))
            else:
                return get_assigned_users_filter(UserStoryModel, value)

        return None


class UserStoriesRoleFilter(filters.BaseRelatedFieldsFilter):
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
                        qs_method(Q(get_assigned_users_filter(user_story_model, memberships)))
                    )

        return filters.FilterBackend.filter_queryset(self, request, queryset, view)


class DashboardFilter(filters.FilterBackend):
    """
    This filter improves performance for dashboard queries.
    Only search in the user projects
    """
    filter_name = 'dashboard'
    param_name = "dashboard"

    def _filter_user_projects(self, request):
        membership_model = apps.get_model('projects', 'Membership')
        if isinstance(request.user, AnonymousUser):
            return None
        else:
            memberships_project_ids = membership_model.objects.filter(user=request.user).values(
                'project_id')

        return Subquery(memberships_project_ids)

    def filter_queryset(self, request, queryset, view):
        if request.QUERY_PARAMS.get(self.param_name, False):
            user_projects_ids_subquery = self._filter_user_projects(request)

            if user_projects_ids_subquery:
                queryset = queryset.filter(project_id__in=user_projects_ids_subquery)

        return super().filter_queryset(request, queryset, view)
