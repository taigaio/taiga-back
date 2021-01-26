# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from django.apps import apps
from django.db import transaction
from django.db.models import Max

from django.utils.translation import ugettext as _
from django.http import HttpResponse

from taiga.base import filters as base_filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base import status
from taiga.base.decorators import list_route
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelListViewSet
from taiga.base.api.utils import get_object_or_404
from taiga.base.utils import json
from taiga.base.utils.db import get_object_or_none

from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.history.services import take_snapshot
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.by_ref import ByRefMixin
from taiga.projects.models import Project, UserStoryStatus, Swimlane
from taiga.projects.notifications.mixins import AssignedUsersSignalMixin
from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.notifications.mixins import WatchersViewSetMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.tagging.api import TaggedResourceMixin
from taiga.projects.votes.mixins.viewsets import VotedResourceMixin
from taiga.projects.votes.mixins.viewsets import VotersViewSetMixin
from taiga.projects.userstories.utils import attach_extra_info

from . import filters
from . import models
from . import permissions
from . import serializers
from . import services
from . import validators


class UserStoryViewSet(AssignedUsersSignalMixin, OCCResourceMixin,
                       VotedResourceMixin, HistoryResourceMixin,
                       WatchedResourceMixin, ByRefMixin, TaggedResourceMixin,
                       BlockedByProjectMixin, ModelCrudViewSet):
    validator_class = validators.UserStoryValidator
    queryset = models.UserStory.objects.all()
    permission_classes = (permissions.UserStoryPermission,)
    filter_backends = (base_filters.CanViewUsFilterBackend,
                       filters.EpicFilter,
                       base_filters.UserStoriesRoleFilter,
                       base_filters.OwnersFilter,
                       base_filters.AssignedToFilter,
                       base_filters.AssignedUsersFilter,
                       base_filters.UserStoryStatusesFilter,
                       base_filters.TagsFilter,
                       base_filters.SwimlanesFilter,
                       base_filters.WatchersFilter,
                       base_filters.QFilter,
                       base_filters.CreatedDateFilter,
                       base_filters.ModifiedDateFilter,
                       base_filters.FinishDateFilter,
                       base_filters.MilestoneEstimatedStartFilter,
                       base_filters.MilestoneEstimatedFinishFilter,
                       base_filters.OrderByFilterMixin)
    filter_fields = ["project",
                     "project__slug",
                     "milestone",
                     "milestone__isnull",
                     "is_closed",
                     "status__is_archived",
                     "status__is_closed"]
    order_by_fields = ["backlog_order",
                       "sprint_order",
                       "kanban_order",
                       "epic_order",
                       "project",
                       "milestone",
                       "status",
                       "created_date",
                       "modified_date",
                       "assigned_to",
                       "subject",
                       "total_voters"]

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.UserStoryNeighborsSerializer

        if self.action == "list" and self.request.QUERY_PARAMS.get('dashboard', False):
            return serializers.UserStoryLightSerializer

        if self.action == "list":
            return serializers.UserStoryListSerializer

        return serializers.UserStorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("project",
                               "status",
                               "assigned_to")

        if not self.request.QUERY_PARAMS.get('dashboard', False):
            qs = qs.select_related("milestone",
                                   "owner",
                                   "generated_from_issue",
                                   "generated_from_task")

            qs = qs.prefetch_related("assigned_users")
            include_attachments = "include_attachments" in self.request.QUERY_PARAMS
            include_tasks = "include_tasks" in self.request.QUERY_PARAMS

            epic_id = self.request.QUERY_PARAMS.get("epic", None)
            # We can be filtering by more than one epic so epic_id can consist
            # of different ids separated by comma. In that situation we will use
            # only the first
            if epic_id is not None:
                epic_id = epic_id.split(",")[0]

            qs = attach_extra_info(qs, user=self.request.user,
                                   include_attachments=include_attachments,
                                   include_tasks=include_tasks,
                                   epic_id=epic_id)
        return qs

    # Updating some attributes of the userstory can affect the ordering in the backlog, kanban or taskboard
    # These three methods generate a key for the user story and can be used to be compared before and after
    # saving. If there is any difference it means an extra ordering update must be done
    def _backlog_order_key(self, obj):
        return f"{obj.project_id}-{obj.backlog_order}"

    def _kanban_order_key(self, obj):
        return f"{obj.project_id}-{obj.swimlane_id}-{obj.status_id}-{obj.kanban_order}"

    def _sprint_order_key(self, obj):
        return f"{obj.project_id}-{obj.milestone_id}-{obj.sprint_order}"

    def _add_taiga_info_headers(self):
        try:
            project_id = int(self.request.QUERY_PARAMS.get("project", None))
        except TypeError:
            project_id = None

        milestone = self.request.QUERY_PARAMS.get("milestone", "").lower()

        if project_id and milestone == "null":
            # Add this header only to draw the backlog (milestone=null)
            total_backlog_userstories = self.queryset.filter(project_id=project_id, milestone__isnull=True).count()
            self.headers["Taiga-Info-Backlog-Total-Userstories"] = total_backlog_userstories

        if project_id:
            # Add this header to show if there are user stories not assigned to any swimlane.
            # Useful to show _Unclassified user stories_ option in swimlane selector at create/edit forms.
            without_swimlane = self.queryset.filter(project_id=project_id, swimlane__isnull=True).exists()
            self.headers["Taiga-Info-Userstories-Without-Swimlane"] = json.dumps(without_swimlane)

    def list(self, request, *args, **kwargs):
        res = super().list(request, *args, **kwargs)
        self._add_taiga_info_headers()
        return res

    def pre_validate(self):
        # ## start-hack-reorder ##
        # Usefull to check if order fields should be updated.
        self._old_backlog_order_key = self._backlog_order_key(self.object)
        self._old_sprint_order_key = self._sprint_order_key(self.object)
        self._old_kanban_order_key = self._kanban_order_key(self.object)
        # ## end-hack-reorder ##

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if obj.milestone_id and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this sprint "
                                         "to this user story."))

        if obj.status_id and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this status "
                                         "to this user story."))

        if obj.swimlane_id and obj.swimlane.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this swimlane "
                                         "to this user story."))

    def pre_save(self, obj):
        # ## start-hack-reorder ##
        if obj.id:
            if self._old_kanban_order_key != self._kanban_order_key(self.object):
                # The user story is moved to other status, swimlane or project.
                # It should be at the end of the cell (swimlanes / status).
                obj.kanban_order = models.UserStory.NEW_KANBAN_ORDER()
        # ## end-hack-reorder ##

        # ## start-hack-rolepoints ##
        # This is very ugly hack, but having
        # restframework is the only way to do it.
        #
        # NOTE: code moved as is from serializer
        #       to api because is not serializer logic.
        related_data = getattr(obj, "_related_data", {})
        self._role_points = related_data.pop("role_points", None)
        # ## end-hack-rolepoints ##

        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    def _reorder_if_needed(self, obj, old_order_key, order_key, order_attr,
                           project, status=None, milestone=None):
        # TODO: The goal should be erase this function.
        #
        # Executes the extra ordering if there is a difference in the  ordering keys
        if old_order_key != order_key:
            data = [{"us_id": obj.id, "order": getattr(obj, order_attr)}]
            return services.update_userstories_order_in_bulk(data,
                                                             order_attr,
                                                             project,
                                                             status=status,
                                                             milestone=milestone)
        return {}

    def post_save(self, obj, created=False):
        # ## start-hack-reorder ##
        # TODO: The goal should be erase this hack.
        if not created:
            # Let's reorder the related stuff after edit the element
            orders_updated = {}
            updated = self._reorder_if_needed(obj,
                                              self._old_backlog_order_key,
                                              self._backlog_order_key(obj),
                                              "backlog_order",
                                              obj.project)
            orders_updated.update(updated)
            updated = self._reorder_if_needed(obj,
                                              self._old_sprint_order_key,
                                              self._sprint_order_key(obj),
                                              "sprint_order",
                                              obj.project,
                                              milestone=obj.milestone)
            orders_updated.update(updated)
            self.headers["Taiga-Info-Order-Updated"] = json.dumps(orders_updated)
        # ## end-hack-reorder ##

        # ## starts-hack-rolepoints ##
        # Code related to the hack of pre_save method.
        # Rather, this is the continuation of it.
        if self._role_points:
            Points = apps.get_model("projects", "Points")
            RolePoints = apps.get_model("userstories", "RolePoints")

            for role_id, points_id in self._role_points.items():
                try:
                    role_points = RolePoints.objects.get(role__id=role_id, user_story_id=obj.pk,
                                                         role__computable=True)
                except (ValueError, RolePoints.DoesNotExist):
                    raise exc.BadRequest({
                        "points": _("Invalid role id '{role_id}'").format(role_id=role_id)
                    })

                try:
                    role_points.points = Points.objects.get(id=points_id, project_id=obj.project_id)
                except (ValueError, Points.DoesNotExist):
                    raise exc.BadRequest({
                        "points": _("Invalid points id '{points_id}'").format(points_id=points_id)
                    })

                role_points.save()
        # ## end-hack-rolepoints ##

        super().post_save(obj, created)

    @transaction.atomic
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)

        # if US has been promoted from issue, add a comment to the origin (issue)
        if response.status_code == status.HTTP_201_CREATED:
            for generated_from in ['generated_from_issue', 'generated_from_task']:
                generator = getattr(self.object, generated_from)
                if generator:
                    generator.save()

                    comment = _("Generating the user story #{ref} - {subject}")
                    comment = comment.format(ref=self.object.ref, subject=self.object.subject)
                    history = take_snapshot(generator,
                                            comment=comment,
                                            user=self.request.user)

                    self.send_notifications(generator, history)

        return response

    def update(self, request, *args, **kwargs):
        self.object = self.get_object_or_none()

        # If you move the US to another project...
        project_id = request.DATA.get('project', None)
        if project_id and self.object and self.object.project.id != project_id:
            try:
                new_project = Project.objects.get(pk=project_id)
                self.check_permissions(request, "destroy", self.object)
                self.check_permissions(request, "create", new_project)

                sprint_id = request.DATA.get('milestone', None)
                if sprint_id is not None and new_project.milestones.filter(pk=sprint_id).count() == 0:
                    request.DATA['milestone'] = None

                swimlane_id = request.DATA.get('swimlane', None)
                if swimlane_id is not None and new_project.swimlanes.filter(pk=swimlane_id).count() == 0:
                    request.DATA['swimlane'] = None

                status_id = request.DATA.get('status', None)
                if status_id is not None:
                    try:
                        old_status = self.object.project.us_statuses.get(pk=status_id)
                        new_status = new_project.us_statuses.get(slug=old_status.slug)
                        request.DATA['status'] = new_status.id
                    except UserStoryStatus.DoesNotExist:
                        request.DATA['status'] = new_project.default_us_status_id
            except Project.DoesNotExist:
                return response.BadRequest(_("The project doesn't exist"))

        return super().update(request, *args, **kwargs)

    @list_route(methods=["GET"])
    def filters_data(self, request, *args, **kwargs):
        project_id = request.QUERY_PARAMS.get("project", None)
        project = get_object_or_404(Project, id=project_id)

        filter_backends = self.get_filter_backends()
        statuses_filter_backends = (f for f in filter_backends if f != base_filters.UserStoryStatusesFilter)
        assigned_to_filter_backends = (f for f in filter_backends if f != base_filters.AssignedToFilter)
        assigned_users_filter_backends = (f for f in filter_backends if f != base_filters.AssignedUsersFilter)
        owners_filter_backends = (f for f in filter_backends if f != base_filters.OwnersFilter)
        epics_filter_backends = (f for f in filter_backends if f != filters.EpicFilter)
        roles_filter_backends = (f for f in filter_backends if f != base_filters.RoleFilter)
        tags_filter_backends = (f for f in filter_backends if f != base_filters.TagsFilter)

        queryset = self.get_queryset()
        # assigned_to is kept for retro-compatibility reasons; but currently filters
        # are using assigned_users
        querysets = {
            "statuses": self.filter_queryset(queryset, filter_backends=statuses_filter_backends),
            "assigned_to": self.filter_queryset(queryset, filter_backends=assigned_to_filter_backends),
            "assigned_users": self.filter_queryset(queryset, filter_backends=assigned_users_filter_backends),
            "owners": self.filter_queryset(queryset, filter_backends=owners_filter_backends),
            "tags": self.filter_queryset(queryset, filter_backends=tags_filter_backends),
            "epics": self.filter_queryset(queryset, filter_backends=epics_filter_backends),
            "roles": self.filter_queryset(queryset, filter_backends=roles_filter_backends)
        }

        return response.Ok(services.get_userstories_filters_data(project, querysets))

    @list_route(methods=["GET"])
    def csv(self, request):
        uuid = request.QUERY_PARAMS.get("uuid", None)
        if uuid is None:
            return response.NotFound()

        project = get_object_or_404(Project, userstories_csv_uuid=uuid)
        queryset = project.user_stories.all().order_by('ref')
        data = services.userstories_to_csv(project, queryset)
        csv_response = HttpResponse(data.getvalue(), content_type='application/csv; charset=utf-8')
        csv_response['Content-Disposition'] = 'attachment; filename="userstories.csv"'
        return csv_response

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        validator = validators.UserStoriesBulkValidator(data=request.DATA)
        if validator.is_valid():
            data = validator.data
            project = Project.objects.get(id=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            if project.blocked_code is not None:
                raise exc.Blocked(_("Blocked element"))

            user_stories = services.create_userstories_in_bulk(
                data["bulk_stories"], project=project, owner=request.user,
                status_id=data.get("status_id") or project.default_us_status_id,
                swimlane_id=data.get("swimlane_id", None),
                callback=self.post_save, precall=self.pre_save)

            user_stories = self.get_queryset().filter(id__in=[i.id for i in user_stories])
            for user_story in user_stories:
                self.persist_history_snapshot(obj=user_story)

            user_stories_serialized = self.get_serializer_class()(user_stories, many=True)

            return response.Ok(user_stories_serialized.data)
        return response.BadRequest(validator.errors)

    @list_route(methods=["POST"])
    def bulk_update_milestone(self, request, **kwargs):
        validator = validators.UpdateMilestoneBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        milestone = get_object_or_404(Milestone, pk=data["milestone_id"])

        self.check_permissions(request, "bulk_update_milestone", project)

        services.update_userstories_milestone_in_bulk(data["bulk_stories"], milestone)
        services.snapshot_userstories_in_bulk(data["bulk_stories"], request.user)

        return response.NoContent()

    def _bulk_update_order(self, order_field, request, **kwargs):
        validator = validators.UpdateUserStoriesOrderBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        status = None
        status_id = data.get("status_id", None)
        if status_id is not None:
            status = get_object_or_404(UserStoryStatus, pk=status_id)

        milestone = None
        milestone_id = data.get("milestone_id", None)
        if milestone_id is not None:
            milestone = get_object_or_404(Milestone, pk=milestone_id)

        self.check_permissions(request, "bulk_update_order", project)
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        ret = services.update_userstories_order_in_bulk(data["bulk_stories"],
                                                        order_field,
                                                        project,
                                                        status=status,
                                                        milestone=milestone)
        return response.Ok(ret)

    @list_route(methods=["POST"])
    def bulk_update_backlog_order(self, request, **kwargs):
        return self._bulk_update_order("backlog_order", request, **kwargs)

    @list_route(methods=["POST"])
    def bulk_update_sprint_order(self, request, **kwargs):
        return self._bulk_update_order("sprint_order", request, **kwargs)

    @list_route(methods=["POST"])
    def bulk_update_kanban_order(self, request, **kwargs):
        # Validate data
        validator = validators.UpdateUserStoriesKanbanOrderBulkValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)
        data = validator.data

        # Get and validate project permissions
        project_id = data["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        self.check_permissions(request, "bulk_update_order", project)
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        # Get status
        status_id = data["status_id"]
        status = get_object_or_404(UserStoryStatus, pk=status_id, project=project)

        # Get swimlane
        swimlane = None
        swimlane_id = data.get("swimlane_id", None)
        if swimlane_id is not None:
            swimlane = get_object_or_404(Swimlane, pk=swimlane_id, project=project)

        # Get after_userstory
        after_userstory = None
        after_userstory_id = data.get("after_userstory_id", None)
        if after_userstory_id is not None:
            after_userstory = get_object_or_404(models.UserStory, pk=after_userstory_id, project=project)

        # Get before_userstory
        before_userstory = None
        before_userstory_id = data.get("before_userstory_id", None)
        if before_userstory_id is not None:
            before_userstory = get_object_or_404(models.UserStory, pk=before_userstory_id, project=project)

        ret = services.update_userstories_kanban_order_in_bulk(project=project,
                                                               status=status,
                                                               swimlane=swimlane,
                                                               after_userstory=after_userstory,
                                                               before_userstory=before_userstory,
                                                               bulk_userstories=data["bulk_userstories"])
        return response.Ok(ret)


class UserStoryVotersViewSet(VotersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.UserStoryVotersPermission,)
    resource_model = models.UserStory


class UserStoryWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.UserStoryWatchersPermission,)
    resource_model = models.UserStory
