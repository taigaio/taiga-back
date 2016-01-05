# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from contextlib import suppress


from django.apps import apps
from django.db import transaction
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base import status
from taiga.base.decorators import list_route
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.utils import get_object_or_404

from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.models import Project, UserStoryStatus
from taiga.projects.history.services import take_snapshot
from taiga.projects.votes.mixins.viewsets import VotedResourceMixin, VotersViewSetMixin

from . import models
from . import permissions
from . import serializers
from . import services


class UserStoryViewSet(OCCResourceMixin, VotedResourceMixin, HistoryResourceMixin, WatchedResourceMixin,
                       ModelCrudViewSet):
    queryset = models.UserStory.objects.all()
    permission_classes = (permissions.UserStoryPermission,)
    filter_backends = (filters.CanViewUsFilterBackend,
                       filters.OwnersFilter,
                       filters.AssignedToFilter,
                       filters.StatusesFilter,
                       filters.TagsFilter,
                       filters.WatchersFilter,
                       filters.QFilter,
                       filters.OrderByFilterMixin)
    retrieve_exclude_filters = (filters.OwnersFilter,
                                filters.AssignedToFilter,
                                filters.StatusesFilter,
                                filters.TagsFilter,
                                filters.WatchersFilter)
    filter_fields = ["project",
                     "milestone",
                     "milestone__isnull",
                     "is_closed",
                     "status__is_archived",
                     "status__is_closed"]
    order_by_fields = ["backlog_order",
                       "sprint_order",
                       "kanban_order",
                       "total_voters"]

    # Specific filter used for filtering neighbor user stories
    _neighbor_tags_filter = filters.TagsFilter('neighbor_tags')

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["retrieve", "by_ref"]:
            return serializers.UserStoryNeighborsSerializer

        if self.action == "list":
            return serializers.UserStoryListSerializer

        return serializers.UserStorySerializer

    def update(self, request, *args, **kwargs):
        self.object = self.get_object_or_none()
        project_id = request.DATA.get('project', None)
        if project_id and self.object and self.object.project.id != project_id:
            try:
                new_project = Project.objects.get(pk=project_id)
                self.check_permissions(request, "destroy", self.object)
                self.check_permissions(request, "create", new_project)

                sprint_id = request.DATA.get('milestone', None)
                if sprint_id is not None and new_project.milestones.filter(pk=sprint_id).count() == 0:
                    request.DATA['milestone'] = None

                status_id = request.DATA.get('status', None)
                if status_id is not None:
                    try:
                        old_status = self.object.project.us_statuses.get(pk=status_id)
                        new_status = new_project.us_statuses.get(slug=old_status.slug)
                        request.DATA['status'] = new_status.id
                    except UserStoryStatus.DoesNotExist:
                        request.DATA['status'] = new_project.default_us_status.id
            except Project.DoesNotExist:
                return response.BadRequest(_("The project doesn't exist"))

        return super().update(request, *args, **kwargs)


    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related("role_points",
                                 "role_points__points",
                                 "role_points__role")
        qs = qs.select_related("milestone",
                               "project",
                               "status",
                               "owner",
                               "assigned_to",
                               "generated_from_issue")
        qs = self.attach_votes_attrs_to_queryset(qs)
        return self.attach_watchers_attrs_to_queryset(qs)

    def pre_save(self, obj):
        # This is very ugly hack, but having
        # restframework is the only way to do it.
        # NOTE: code moved as is from serializer
        # to api because is not serializer logic.
        related_data = getattr(obj, "_related_data", {})
        self._role_points = related_data.pop("role_points", None)

        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    def post_save(self, obj, created=False):
        # Code related to the hack of pre_save method. Rather,
        # this is the continuation of it.

        Points = apps.get_model("projects", "Points")
        RolePoints = apps.get_model("userstories", "RolePoints")

        if self._role_points:
            with suppress(ObjectDoesNotExist):
                for role_id, points_id in self._role_points.items():
                    role_points = RolePoints.objects.get(role__id=role_id, user_story_id=obj.pk)
                    role_points.points = Points.objects.get(id=points_id, project_id=obj.project_id)
                    role_points.save()

        super().post_save(obj, created)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this sprint "
                                         "to this user story."))

        if obj.status and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions to set this status "
                                         "to this user story."))

    @list_route(methods=["GET"])
    def filters_data(self, request, *args, **kwargs):
        project_id = request.QUERY_PARAMS.get("project", None)
        project = get_object_or_404(Project, id=project_id)

        filter_backends = self.get_filter_backends()
        statuses_filter_backends = (f for f in filter_backends if f != filters.StatusesFilter)
        assigned_to_filter_backends = (f for f in filter_backends if f != filters.AssignedToFilter)
        owners_filter_backends = (f for f in filter_backends if f != filters.OwnersFilter)
        tags_filter_backends = (f for f in filter_backends if f != filters.TagsFilter)

        queryset = self.get_queryset()
        querysets = {
            "statuses": self.filter_queryset(queryset, filter_backends=statuses_filter_backends),
            "assigned_to": self.filter_queryset(queryset, filter_backends=assigned_to_filter_backends),
            "owners": self.filter_queryset(queryset, filter_backends=owners_filter_backends),
            "tags": self.filter_queryset(queryset)
        }
        return response.Ok(services.get_userstories_filters_data(project, querysets))

    @list_route(methods=["GET"])
    def by_ref(self, request):
        ref = request.QUERY_PARAMS.get("ref", None)
        project_id = request.QUERY_PARAMS.get("project", None)
        userstory = get_object_or_404(models.UserStory, ref=ref, project_id=project_id)
        return self.retrieve(request, pk=userstory.pk)

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
        serializer = serializers.UserStoriesBulkSerializer(data=request.DATA)
        if serializer.is_valid():
            data = serializer.data
            project = Project.objects.get(id=data["project_id"])
            self.check_permissions(request, 'bulk_create', project)
            user_stories = services.create_userstories_in_bulk(
                data["bulk_stories"], project=project, owner=request.user,
                status_id=data.get("status_id") or project.default_us_status_id,
                callback=self.post_save, precall=self.pre_save)
            user_stories_serialized = self.get_serializer_class()(user_stories, many=True)
            return response.Ok(user_stories_serialized.data)
        return response.BadRequest(serializer.errors)

    def _bulk_update_order(self, order_field, request, **kwargs):
        serializer = serializers.UpdateUserStoriesOrderBulkSerializer(data=request.DATA)
        if not serializer.is_valid():
            return response.BadRequest(serializer.errors)

        data = serializer.data
        project = get_object_or_404(Project, pk=data["project_id"])

        self.check_permissions(request, "bulk_update_order", project)
        services.update_userstories_order_in_bulk(data["bulk_stories"],
                                                  project=project,
                                                  field=order_field)
        services.snapshot_userstories_in_bulk(data["bulk_stories"], request.user)

        return response.NoContent()

    @list_route(methods=["POST"])
    def bulk_update_backlog_order(self, request, **kwargs):
        return self._bulk_update_order("backlog_order", request, **kwargs)

    @list_route(methods=["POST"])
    def bulk_update_sprint_order(self, request, **kwargs):
        return self._bulk_update_order("sprint_order", request, **kwargs)

    @list_route(methods=["POST"])
    def bulk_update_kanban_order(self, request, **kwargs):
        return self._bulk_update_order("kanban_order", request, **kwargs)

    @transaction.atomic
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)

        # Added comment to the origin (issue)
        if response.status_code == status.HTTP_201_CREATED and self.object.generated_from_issue:
            self.object.generated_from_issue.save()

            comment = _("Generating the user story #{ref} - {subject}")
            comment = comment.format(ref=self.object.ref, subject=self.object.subject)
            history = take_snapshot(self.object.generated_from_issue,
                                    comment=comment,
                                    user=self.request.user)

            self.send_notifications(self.object.generated_from_issue, history)

        return response

class UserStoryVotersViewSet(VotersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.UserStoryVotersPermission,)
    resource_model = models.UserStory


class UserStoryWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.UserStoryWatchersPermission,)
    resource_model = models.UserStory
