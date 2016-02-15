# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils.db import to_tsquery

logger = logging.getLogger(__name__)



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

        return super().filter_queryset(request, queryset.order_by(raw_fieldname), view)


class FilterBackend(OrderByFilterMixin):
    """
    Default filter backend.
    """
    pass


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

        if request.user.is_authenticated() and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated():
            membership_model = apps.get_model('projects', 'Membership')
            memberships_qs = membership_model.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)
            memberships_qs = memberships_qs.filter(Q(role__permissions__contains=[self.permission]) |
                                                   Q(is_admin=True))

            projects_list = [membership.project_id for membership in memberships_qs]

            qs = qs.filter(Q(project_id__in=projects_list) |
                           Q(project__public_permissions__contains=[self.permission]))
        else:
            qs = qs.filter(project__anon_permissions__contains=[self.permission])

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


#####################################################################
# Attachments filters
#####################################################################

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

        if request.user.is_authenticated() and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated():
            Membership = apps.get_model('projects', 'Membership')
            memberships_qs = Membership.objects.filter(user=request.user)
            if project_id:
                memberships_qs = memberships_qs.filter(project_id=project_id)
            memberships_qs = memberships_qs.filter(Q(role__permissions__contains=[self.permission]) |
                                                   Q(is_admin=True))

            projects_list = [membership.project_id for membership in memberships_qs]

            if project:
                is_member = project.id in projects_list
                has_project_public_view_permission = "view_project" in project.public_permissions
                if not is_member and not has_project_public_view_permission:
                    qs = qs.none()

            q = Q(memberships__project_id__in=projects_list) | Q(id=request.user.id)

            #If there is no selected project we want access to users from public projects
            if not project:
                q = q | Q(memberships__project__public_permissions__contains=[self.permission])

            qs = qs.filter(q)

        else:
            if project and not "view_project" in project.anon_permissions:
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

        if request.user.is_authenticated() and request.user.is_superuser:
            return None

        if not request.user.is_authenticated():
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

        return super().filter_queryset(request, queryset.distinct(), view)


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
    def __init__(self, filter_name=None):
        if filter_name:
            self.filter_name = filter_name

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

    def _get_queryparams(self, params):
        raw_value = params.get(self.filter_name, None)

        if raw_value:
            value = self._prepare_filter_data(raw_value)

            if None in value:
                qs_in_kwargs = {"{}__in".format(self.filter_name): [v for v in value if v is not None]}
                qs_isnull_kwargs = {"{}__isnull".format(self.filter_name): True}
                return Q(**qs_in_kwargs) | Q(**qs_isnull_kwargs)
            else:
                return {"{}__in".format(self.filter_name): value}

        return None

    def filter_queryset(self, request, queryset, view):
        query = self._get_queryparams(request.QUERY_PARAMS)
        if query:
            if isinstance(query, dict):
                queryset = queryset.filter(**query)
            else:
                queryset = queryset.filter(query)

        return super().filter_queryset(request, queryset, view)


class OwnersFilter(BaseRelatedFieldsFilter):
    filter_name = 'owner'


class AssignedToFilter(BaseRelatedFieldsFilter):
    filter_name = 'assigned_to'


class StatusesFilter(BaseRelatedFieldsFilter):
    filter_name = 'status'


class IssueTypesFilter(BaseRelatedFieldsFilter):
    filter_name = 'type'


class PrioritiesFilter(BaseRelatedFieldsFilter):
    filter_name = 'priority'


class SeveritiesFilter(BaseRelatedFieldsFilter):
    filter_name = 'severity'


class TagsFilter(FilterBackend):
    filter_name = 'tags'

    def __init__(self, filter_name=None):
        if filter_name:
            self.filter_name = filter_name

    def _get_tags_queryparams(self, params):
        tags = params.get(self.filter_name, None)
        if tags:
            return tags.split(",")

        return None

    def filter_queryset(self, request, queryset, view):
        query_tags = self._get_tags_queryparams(request.QUERY_PARAMS)
        if query_tags:
            queryset = queryset.filter(tags__contains=query_tags)

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
        model = queryset.model
        if query_watchers:
            WatchedModel = apps.get_model("notifications", "Watched")
            watched_type = ContentType.objects.get_for_model(queryset.model)

            try:
                watched_ids = WatchedModel.objects.filter(content_type=watched_type, user__id__in=query_watchers).values_list("object_id", flat=True)
                queryset = queryset.filter(id__in=watched_ids)
            except ValueError:
                raise exc.BadRequest(_("Error in filter params types."))

        return super().filter_queryset(request, queryset, view)


#####################################################################
# Text search filters
#####################################################################

class QFilter(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        q = request.QUERY_PARAMS.get('q', None)
        if q:
            table = queryset.model._meta.db_table
            where_clause = ("""
                to_tsvector('english_nostop',
                            coalesce({table}.subject, '') || ' ' ||
                            coalesce({table}.ref) || ' ' ||
                            coalesce({table}.description, '')) @@ to_tsquery('english_nostop', %s)
            """.format(table=table))

            queryset = queryset.extra(where=[where_clause], params=[to_tsquery(q)])

        return queryset
