# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid
import functools
from easy_thumbnails.source_generators import pil_image
from dateutil.relativedelta import relativedelta

from django.apps import apps
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils import timezone

from django_pglocks import advisory_lock

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.api import ModelCrudViewSet, ModelListViewSet, ModelUpdateRetrieveViewSet
from taiga.base.api.mixins import BlockedByProjectMixin, BlockeableSaveMixin, BlockeableDeleteMixin
from taiga.base.api.permissions import AllowAnyPermission
from taiga.base.api.utils import get_object_or_error
from taiga.base.api.viewsets import ViewSet
from taiga.base.decorators import list_route
from taiga.base.decorators import detail_route
from taiga.base.utils.slug import slugify_uniquely

from taiga.permissions import services as permissions_services

from taiga.projects.epics.models import Epic
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.issues.models import Issue
from taiga.projects.likes.mixins.viewsets import LikedResourceMixin, FansViewSetMixin
from taiga.projects.notifications.apps import signal_members_added
from taiga.projects.notifications.mixins import WatchersViewSetMixin
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.mixins.on_destroy import MoveOnDestroyMixin, MoveOnDestroySwimlaneMixin
from taiga.projects.mixins.ordering import BulkUpdateOrderMixin
from taiga.projects.signals import issue_status_post_move_on_destroy as issue_status_post_move_on_destroy_signal
from taiga.projects.tasks.models import Task
from taiga.projects.tagging.api import TagsColorsResourceMixin
from taiga.projects.userstories.models import UserStory, RolePoints
from taiga.projects.userstories.services import reset_userstories_kanban_order_in_bulk

from . import filters as project_filters
from . import models
from . import permissions
from . import serializers
from . import validators
from . import services
from . import utils as project_utils
from . import throttling

######################################################
# Project
######################################################
from ..base.exceptions import NotAuthenticated


class ProjectViewSet(LikedResourceMixin, HistoryResourceMixin,
                     BlockeableSaveMixin, BlockeableDeleteMixin,
                     TagsColorsResourceMixin, ModelCrudViewSet):
    validator_class = validators.ProjectValidator
    queryset = models.Project.objects.all()
    permission_classes = (permissions.ProjectPermission, )
    filter_backends = (project_filters.UserOrderFilterBackend,
                       project_filters.QFilterBackend,
                       project_filters.CanViewProjectObjFilterBackend,
                       project_filters.DiscoverModeFilterBackend)

    filter_fields = (("member", "members"),
                     "is_looking_for_people",
                     "is_featured",
                     "is_backlog_activated",
                     "is_kanban_activated")

    ordering = ("name", "id")
    order_by_fields = ("total_fans",
                       "total_fans_last_week",
                       "total_fans_last_month",
                       "total_fans_last_year",
                       "total_activity",
                       "total_activity_last_week",
                       "total_activity_last_month",
                       "total_activity_last_year")

    def is_blocked(self, obj):
        return obj.blocked_code is not None

    def _get_order_by_field_name(self):
        order_by_query_param = project_filters.CanViewProjectObjFilterBackend.order_by_query_param
        order_by = self.request.QUERY_PARAMS.get(order_by_query_param, None)
        if order_by is not None and order_by.startswith("-"):
            return order_by[1:]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("owner")
        if self.request.QUERY_PARAMS.get('discover_mode', False):
            qs = project_utils.attach_members(qs)
            qs = project_utils.attach_notify_policies(qs)
            qs = project_utils.attach_is_fan(qs, user=self.request.user)
            qs = project_utils.attach_my_role_permissions(qs, user=self.request.user)
            qs = project_utils.attach_closed_milestones(qs)
            qs = project_utils.attach_my_homepage(qs, user=self.request.user)
        elif self.request.QUERY_PARAMS.get('slight', False):
            qs = project_utils.attach_basic_info(qs, user=self.request.user)
        else:
            qs = project_utils.attach_extra_info(qs, user=self.request.user)

        # If filtering an activity period we must exclude the activities not updated recently enough
        now = timezone.now()
        order_by_field_name = self._get_order_by_field_name()
        if order_by_field_name == "total_fans_last_week":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(weeks=1))
        elif order_by_field_name == "total_fans_last_month":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(months=1))
        elif order_by_field_name == "total_fans_last_year":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(years=1))
        elif order_by_field_name == "total_activity_last_week":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(weeks=1))
        elif order_by_field_name == "total_activity_last_month":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(months=1))
        elif order_by_field_name == "total_activity_last_year":
            qs = qs.filter(totals_updated_datetime__gte=now - relativedelta(years=1))

        return qs

    def retrieve(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if self.action == "by_slug":
            self.lookup_field = "slug"
            # If we retrieve the project by slug we want to filter by user the
            # permissions and return 404 in case the user don't have access
            flt = filters.get_filter_expression_can_view_projects(request.user)

            qs = qs.filter(flt)

        self.object = get_object_or_error(qs, request.user, **kwargs)

        self.check_permissions(request, 'retrieve', self.object)

        if self.object is None:
            raise Http404

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def get_serializer_class(self):
        if self.action == "list" and self.request.QUERY_PARAMS.get('slight', False):
            return serializers.ProjectLightSerializer
        if self.action == "list":
            return serializers.ProjectSerializer

        return serializers.ProjectDetailSerializer

    @detail_route(methods=["POST"])
    def change_logo(self, request, *args, **kwargs):
        """
        Change logo to this project.
        """
        self.object = get_object_or_error(self.get_queryset(), request.user, **kwargs)
        self.check_permissions(request, "change_logo", self.object)

        logo = request.FILES.get('logo', None)
        if not logo:
            raise exc.WrongArguments(_("Incomplete arguments"))
        try:
            pil_image(logo)
        except Exception:
            raise exc.WrongArguments(_("Invalid image format"))

        self.pre_conditions_on_save(self.object)

        self.object.logo = logo
        self.object.save(update_fields=["logo"])

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    @detail_route(methods=["POST"])
    def remove_logo(self, request, *args, **kwargs):
        """
        Remove the logo of a project.
        """
        self.object = get_object_or_error(self.get_queryset(), request.user, **kwargs)
        self.check_permissions(request, "remove_logo", self.object)
        self.pre_conditions_on_save(self.object)
        self.object.logo = None
        self.object.save(update_fields=["logo"])

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    @detail_route(methods=["POST"])
    def watch(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "watch", project)
        self.pre_conditions_on_save(project)
        notify_level = request.DATA.get("notify_level", NotifyLevel.involved)
        project.add_watcher(self.request.user, notify_level=notify_level)
        return response.Ok()

    @detail_route(methods=["POST"])
    def unwatch(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "unwatch", project)
        self.pre_conditions_on_save(project)
        user = self.request.user
        project.remove_watcher(user)
        return response.Ok()

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        if self.request.user.is_anonymous:
            return response.Unauthorized()

        validator = validators.UpdateProjectOrderBulkValidator(data=request.DATA, many=True)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        services.update_projects_order_in_bulk(data, "user_order", request.user)
        return response.NoContent(data=None)

    @detail_route(methods=["POST"])
    def create_template(self, request, **kwargs):
        template_name = request.DATA.get('template_name', None)
        template_description = request.DATA.get('template_description', None)

        if not template_name:
            raise response.BadRequest(_("Invalid template name"))

        if not template_description:
            raise response.BadRequest(_("Invalid template description"))

        with advisory_lock("create-project-template"):
            template_slug = slugify_uniquely(template_name, models.ProjectTemplate)

            project = self.get_object()

            self.check_permissions(request, 'create_template', project)

            template = models.ProjectTemplate(
                name=template_name,
                slug=template_slug,
                description=template_description,
            )

            template.load_data_from_project(project)

            template.save()
        return response.Created(serializers.ProjectTemplateSerializer(template).data)

    @detail_route(methods=['POST'])
    def leave(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'leave', project)
        self.pre_conditions_on_save(project)
        services.remove_user_from_project(request.user, project)
        return response.Ok()

    def _regenerate_csv_uuid(self, project, field):
        uuid_value = uuid.uuid4().hex
        setattr(project, field, uuid_value)
        project.save()
        return uuid_value

    def _delete_csv_uuid(self, project, field):
        setattr(project, field, None)
        project.save()
        return getattr(project, field)

    @detail_route(methods=["POST"])
    def regenerate_epics_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_epics_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._regenerate_csv_uuid(project, "epics_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def regenerate_userstories_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_userstories_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._regenerate_csv_uuid(project, "userstories_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def regenerate_tasks_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_tasks_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._regenerate_csv_uuid(project, "tasks_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def regenerate_issues_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "regenerate_issues_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._regenerate_csv_uuid(project, "issues_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def delete_epics_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "delete_epics_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._delete_csv_uuid(project, "epics_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def delete_userstories_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "delete_userstories_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._delete_csv_uuid(project, "userstories_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def delete_tasks_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "delete_tasks_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._delete_csv_uuid(project, "tasks_csv_uuid")}
        return response.Ok(data)

    @detail_route(methods=["POST"])
    def delete_issues_csv_uuid(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "delete_issues_csv_uuid", project)
        self.pre_conditions_on_save(project)
        data = {"uuid": self._delete_csv_uuid(project, "issues_csv_uuid")}
        return response.Ok(data)

    @list_route(methods=["GET"])
    def by_slug(self, request, *args, **kwargs):
        slug = request.QUERY_PARAMS.get("slug", None)

        return self.retrieve(request, slug=slug)

    @detail_route(methods=["GET", "PATCH"])
    def modules(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, 'modules', project)
        modules_config = services.get_modules_config(project)

        if request.method == "GET":
            return response.Ok(modules_config.config)

        else:
            self.pre_conditions_on_save(project)
            modules_config.config.update(request.DATA)
            modules_config.save()
            return response.NoContent()

    @detail_route(methods=["GET"])
    def stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "stats", project)
        return response.Ok(services.get_stats_for_project(project))

    @detail_route(methods=["GET"])
    def member_stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "member_stats", project)
        return response.Ok(services.get_member_stats_for_project(project))

    @detail_route(methods=["GET"])
    def issues_stats(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "issues_stats", project)
        return response.Ok(services.get_stats_for_project_issues(project))

    @detail_route(methods=["POST"])
    def transfer_validate_token(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "transfer_validate_token", project)
        token = request.DATA.get('token', None)
        services.transfer.validate_project_transfer_token(token, project, request.user)
        return response.Ok()

    @detail_route(methods=["POST"])
    def transfer_request(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "transfer_request", project)
        services.request_project_transfer(project, request.user)
        return response.Ok()

    @detail_route(methods=['post'])
    def transfer_start(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "transfer_start", project)

        user_id = request.DATA.get('user', None)
        if user_id is None:
            raise exc.WrongArguments(_("Invalid user id"))

        user_model = apps.get_model("users", "User")
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist:
            return response.BadRequest(_("The user doesn't exist"))

        # Check the user is a membership from the project
        if not project.memberships.filter(user=user).exists():
            return response.BadRequest(_("The user must already be a project member"))

        reason = request.DATA.get('reason', None)
        services.start_project_transfer(project, user, reason)
        return response.Ok()

    @detail_route(methods=["POST"])
    def transfer_accept(self, request, pk=None):
        token = request.DATA.get('token', None)
        if token is None:
            raise exc.WrongArguments(_("Invalid token"))

        project = self.get_object()
        self.check_permissions(request, "transfer_accept", project)

        (can_transfer, error_message, total_members) = services.check_if_project_can_be_transfered(
            project,
            request.user,
        )
        if not can_transfer:
            raise exc.NotEnoughSlotsForProject(project.is_private, total_members, error_message)

        reason = request.DATA.get('reason', None)
        services.accept_project_transfer(project, request.user, token, reason)
        return response.Ok()

    @detail_route(methods=["POST"])
    def transfer_reject(self, request, pk=None):
        token = request.DATA.get('token', None)
        if token is None:
            raise exc.WrongArguments(_("Invalid token"))

        project = self.get_object()
        self.check_permissions(request, "transfer_reject", project)

        reason = request.DATA.get('reason', None)
        services.reject_project_transfer(project, request.user, token, reason)
        return response.Ok()

    @detail_route(methods=["POST"])
    def duplicate(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "duplicate", project)
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        validator = validators.DuplicateProjectValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        new_name = data.get("name", "")
        new_description = data.get("description", "")
        new_owner = self.request.user
        new_is_private = data.get('is_private', False)
        new_members = data.get("users", [])

        # Validate if the project can be imported
        (enough_slots, error_message, total_members) = services.check_if_project_can_be_duplicate(
            project=project,
            new_owner=new_owner,
            new_is_private=new_is_private,
            new_user_id_members=[m["id"] for m in new_members]
        )
        if not enough_slots:
            raise exc.NotEnoughSlotsForProject(new_is_private, total_members, error_message)

        new_project = services.duplicate_project(
            project=project,
            name=new_name,
            description=new_description,
            owner=new_owner,
            is_private=new_is_private,
            users=new_members
        )
        new_project = get_object_or_error(self.get_queryset(), request.user, id=new_project.id)
        serializer = self.get_serializer(new_project)
        return response.Created(serializer.data)

    def _raise_if_blocked(self, project):
        if self.is_blocked(project):
            raise exc.Blocked(_("Blocked element"))

    def _set_base_permissions(self, obj):
        update_permissions = False
        if not obj.id:
            if not obj.is_private:
                # Creating a public project
                update_permissions = True
        else:
            if self.get_object().is_private != obj.is_private:
                # Changing project public state
                update_permissions = True

        if update_permissions:
            permissions_services.set_base_permissions_for_project(obj)

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user
            obj.template = self.request.QUERY_PARAMS.get('template', None)

        if not obj.id or self.get_object().is_private != obj.is_private:
            # Validate if the owner have enough slots to create the project
            # or if you are changing the privacy
            (can_create_or_update, error_message, total_members) = services.check_if_project_can_be_created_or_updated(obj)
            if not can_create_or_update:
                raise exc.NotEnoughSlotsForProject(obj.is_private, total_members or 1, error_message)

        self._set_base_permissions(obj)
        super().pre_save(obj)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object_or_none()
        self.check_permissions(request, 'destroy', obj)

        if obj is None:
            raise Http404

        self.pre_delete(obj)
        self.pre_conditions_on_delete(obj)

        services.orphan_project(obj)
        if settings.CELERY_ENABLED:
            services.delete_project.delay(obj.id)
        else:
            services.delete_project(obj.id)

        return response.NoContent()


class DeleteOwnProjectsViewSet(ViewSet):
    def create(self, request, *args, **kwargs):
        projects = models.Project.objects.filter(owner=request.user, is_private=True)
        for project in projects:
            services.orphan_project(project)

        if settings.CELERY_ENABLED:
            services.delete_projects.delay(projects)
        else:
            services.delete_projects(projects)

        return response.NoContent()


class ProjectFansViewSet(FansViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.ProjectFansPermission,)
    resource_model = models.Project


class ProjectWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.ProjectWatchersPermission,)
    resource_model = models.Project


######################################################
## Custom values for selectors
######################################################

class EpicStatusViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                        ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.EpicStatus
    serializer_class = serializers.EpicStatusSerializer
    validator_class = validators.EpicStatusValidator
    permission_classes = (permissions.EpicStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_epic_statuses"
    bulk_update_perm = "change_epicstatus"
    bulk_update_order_action = services.bulk_update_epic_status_order
    move_on_destroy_related_class = Epic
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_epic_status"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("epic-status-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class UserStoryStatusViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                             ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.UserStoryStatus
    serializer_class = serializers.UserStoryStatusSerializer
    validator_class = validators.UserStoryStatusValidator
    permission_classes = (permissions.UserStoryStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_userstory_statuses"
    bulk_update_perm = "change_userstorystatus"
    bulk_update_order_action = services.bulk_update_userstory_status_order
    move_on_destroy_related_class = UserStory
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_us_status"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("epic-user-story-status-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def move_on_destroy_reorder_after_moved(self, moved_to_obj, moved_objs_queryset):
        project = moved_to_obj.project
        bulk_userstories_ids = (moved_objs_queryset.order_by('swimlane__order', 'kanban_order')
                                                   .values_list('id', flat=True))
        reset_userstories_kanban_order_in_bulk(project, bulk_userstories_ids)


class PointsViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                    ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.Points
    serializer_class = serializers.PointsSerializer
    validator_class = validators.PointsValidator
    permission_classes = (permissions.PointsPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_points"
    bulk_update_perm = "change_points"
    bulk_update_order_action = services.bulk_update_points_order
    move_on_destroy_related_class = RolePoints
    move_on_destroy_related_field = "points"
    move_on_destroy_project_default_field = "default_points"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("points-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class SwimlaneViewSet(MoveOnDestroySwimlaneMixin, BlockedByProjectMixin,
                      ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.Swimlane
    serializer_class = serializers.SwimlaneSerializer
    validator_class = validators.SwimlaneValidator
    permission_classes = (permissions.SwimlanePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)
    bulk_update_param = "bulk_swimlanes"
    bulk_update_perm = "change_swimlanes"
    bulk_update_order_action = services.bulk_update_swimlane_order

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("swimlane-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def post_save(self, object, created=False):
        super().post_save(object, created=created)

        if not created:
            return

        # If it's a creation and it's the first and only swimlane,
        # then assign all Userstories to this new swimlane
        total_swimlanes = object.project.swimlanes.count()
        if total_swimlanes == 1:
            uss = object.project.user_stories.all()
            uss.update(swimlane=object)

    def pre_delete(self, obj):
        if obj.project.default_swimlane_id == obj.id and obj.project.swimlanes.count() > 1:
            raise exc.BadRequest(_("The default swimlane cannot be deleted."))


class SwimlaneUserStoryStatusViewSet(BlockedByProjectMixin, ModelListViewSet, ModelUpdateRetrieveViewSet):
    model = models.SwimlaneUserStoryStatus
    serializer_class = serializers.SwimlaneUserStoryStatusSerializer
    validator_class = validators.SwimlaneUserStoryStatusValidator
    permission_classes = (permissions.SwimlaneUserStoryStatusPermission,)
    filter_backends = (filters.custom_filter_class(filters.CanViewProjectFilterBackend,
                                                   project_query_param="status__project"),)
    filter_fields = ('project',)


class UserStoryDueDateViewSet(BlockedByProjectMixin, ModelCrudViewSet):

    model = models.UserStoryDueDate
    serializer_class = serializers.UserStoryDueDateSerializer
    validator_class = validators.UserStoryDueDateValidator
    permission_classes = (permissions.UserStoryDueDatePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("user-story-due-date-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def pre_delete(self, obj):
        if obj.by_default:
            raise exc.BadRequest(
                _("You can't delete the default due date status of a user story"))

    @list_route(methods=["POST"])
    def create_default(self, request, **kwargs):
        context = {
            "request": request
        }
        validator = validators.DueDatesCreationValidator(data=request.DATA,
                                                         context=context)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        project_id = request.DATA.get('project_id')
        project = models.Project.objects.get(id=project_id)

        if project.us_duedates.all():
            raise exc.BadRequest(_("Project does already have due dates"))

        project_template = models.ProjectTemplate.objects.get(
            id=project.creation_template.id)

        for us_duedate in project_template.us_duedates:
            models.UserStoryDueDate.objects.create(
                name=us_duedate["name"],
                by_default=us_duedate["by_default"],
                color=us_duedate["color"],
                days_to_due=us_duedate["days_to_due"],
                order=us_duedate["order"],
                project=project
            )
        project.save()

        serializer = self.get_serializer(project.us_duedates.all(), many=True)

        return response.Ok(serializer.data)


class TaskStatusViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                        ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.TaskStatus
    serializer_class = serializers.TaskStatusSerializer
    validator_class = validators.TaskStatusValidator
    permission_classes = (permissions.TaskStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_task_statuses"
    bulk_update_perm = "change_taskstatus"
    bulk_update_order_action = services.bulk_update_task_status_order
    move_on_destroy_related_class = Task
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_task_status"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("task-status-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class TaskDueDateViewSet(BlockedByProjectMixin, ModelCrudViewSet):

    model = models.TaskDueDate
    serializer_class = serializers.TaskDueDateSerializer
    validator_class = validators.TaskDueDateValidator
    permission_classes = (permissions.TaskDueDatePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("task-due-date-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def pre_delete(self, obj):
        if obj.by_default:
            raise exc.BadRequest(
                _("You can't delete the default due date status of a task"))

    @list_route(methods=["POST"])
    def create_default(self, request, **kwargs):
        context = {
            "request": request
        }
        validator = validators.DueDatesCreationValidator(data=request.DATA,
                                                         context=context)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        project_id = request.DATA.get('project_id')
        project = models.Project.objects.get(id=project_id)

        if project.task_duedates.all():
            raise exc.BadRequest(_("Project does already have task due dates"))

        project_template = models.ProjectTemplate.objects.get(
            id=project.creation_template.id)

        for task_duedate in project_template.task_duedates:
            models.TaskDueDate.objects.create(
                name=task_duedate["name"],
                by_default=task_duedate["by_default"],
                color=task_duedate["color"],
                days_to_due=task_duedate["days_to_due"],
                order=task_duedate["order"],
                project=project
            )
        project.save()

        serializer = self.get_serializer(project.task_duedates.all(),
                                         many=True)

        return response.Ok(serializer.data)


class SeverityViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                      ModelCrudViewSet, BulkUpdateOrderMixin):

    model = models.Severity
    serializer_class = serializers.SeveritySerializer
    validator_class = validators.SeverityValidator
    permission_classes = (permissions.SeverityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_severities"
    bulk_update_perm = "change_severity"
    bulk_update_order_action = services.bulk_update_severity_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "severity"
    move_on_destroy_project_default_field = "default_severity"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("severity-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class PriorityViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                      ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.Priority
    serializer_class = serializers.PrioritySerializer
    validator_class = validators.PriorityValidator
    permission_classes = (permissions.PriorityPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_priorities"
    bulk_update_perm = "change_priority"
    bulk_update_order_action = services.bulk_update_priority_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "priority"
    move_on_destroy_project_default_field = "default_priority"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("priority-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class IssueTypeViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                       ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueType
    serializer_class = serializers.IssueTypeSerializer
    validator_class = validators.IssueTypeValidator
    permission_classes = (permissions.IssueTypePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_types"
    bulk_update_perm = "change_issuetype"
    bulk_update_order_action = services.bulk_update_issue_type_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "type"
    move_on_destroy_project_default_field = "default_issue_type"

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("issue-type-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class IssueStatusViewSet(MoveOnDestroyMixin, BlockedByProjectMixin,
                         ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueStatus
    serializer_class = serializers.IssueStatusSerializer
    validator_class = validators.IssueStatusValidator
    permission_classes = (permissions.IssueStatusPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_statuses"
    bulk_update_perm = "change_issuestatus"
    bulk_update_order_action = services.bulk_update_issue_status_order
    move_on_destroy_related_class = Issue
    move_on_destroy_related_field = "status"
    move_on_destroy_project_default_field = "default_issue_status"
    move_on_destroy_post_destroy_signal = issue_status_post_move_on_destroy_signal

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("issue-status-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)


class IssueDueDateViewSet(BlockedByProjectMixin, ModelCrudViewSet):

    model = models.IssueDueDate
    serializer_class = serializers.IssueDueDateSerializer
    validator_class = validators.IssueDueDateValidator
    permission_classes = (permissions.IssueDueDatePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ('project',)

    def create(self, request, *args, **kwargs):
        project_id = request.DATA.get("project", 0)
        with advisory_lock("issue-due-date-creation-{}".format(project_id)):
            return super().create(request, *args, **kwargs)

    def pre_delete(self, obj):
        if obj.by_default:
            raise exc.BadRequest(
                _("You can't delete the default due date status of an issue"))

    @list_route(methods=["POST"])
    def create_default(self, request, **kwargs):
        context = {
            "request": request
        }
        validator = validators.DueDatesCreationValidator(data=request.DATA,
                                                         context=context)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        project_id = request.DATA.get('project_id')
        project = models.Project.objects.get(id=project_id)

        if project.issue_duedates.all():
            raise exc.BadRequest(_("Project does already have issue due dates"))

        project_template = models.ProjectTemplate.objects.get(
            id=project.creation_template.id)

        for issue_duedate in project_template.issue_duedates:
            models.IssueDueDate.objects.create(
                name=issue_duedate["name"],
                by_default=issue_duedate["by_default"],
                color=issue_duedate["color"],
                days_to_due=issue_duedate["days_to_due"],
                order=issue_duedate["order"],
                project=project
            )
        project.save()

        serializer = self.get_serializer(project.issue_duedates.all(),
                                         many=True)

        return response.Ok(serializer.data)


######################################################
## Project Template
######################################################

class ProjectTemplateViewSet(ModelCrudViewSet):
    model = models.ProjectTemplate
    serializer_class = serializers.ProjectTemplateSerializer
    validator_class = validators.ProjectTemplateValidator
    permission_classes = (permissions.ProjectTemplatePermission,)

    def get_queryset(self):
        return models.ProjectTemplate.objects.all()


######################################################
## Members & Invitations
######################################################

class MembershipViewSet(BlockedByProjectMixin, ModelCrudViewSet):
    model = models.Membership
    admin_serializer_class = serializers.MembershipAdminSerializer
    serializer_class = serializers.MembershipSerializer
    validator_class = validators.MembershipValidator
    permission_classes = (permissions.MembershipPermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project", "role")
    throttle_classes = (throttling.MembershipsRateThrottle,)

    def get_serializer_class(self):
        use_admin_serializer = False

        if self.action == "create":
            use_admin_serializer = True

        if self.action == "retrieve":
            use_admin_serializer = permissions_services.is_project_admin(self.request.user, self.object.project)

        project_id = self.request.QUERY_PARAMS.get("project", None)
        if self.action == "list" and project_id is not None:
            project = get_object_or_error(models.Project, self.request.user, pk=project_id)
            use_admin_serializer = permissions_services.is_project_admin(self.request.user, project)

        if use_admin_serializer:
            return self.admin_serializer_class

        else:
            return self.serializer_class

    def _check_if_new_member_can_be_created(self, membership):
        (can_add_memberships, error_type, total_memberships) = services.check_if_new_member_can_be_created(
            membership
        )
        if not can_add_memberships:
            raise exc.NotEnoughSlotsForProject(
                membership.project.is_private,
                total_memberships,
                error_type
            )

    def _check_if_new_members_can_be_created(self, project, memberships):
        (can_add_memberships, error_type, total_memberships) = services.check_if_new_members_can_be_created(
            project,
            memberships
        )
        if not can_add_memberships:
            raise exc.NotEnoughSlotsForProject(
                project.is_private,
                total_memberships,
                error_type
            )

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        context = {
            "request": request
        }
        validator = validators.MembersBulkValidator(data=request.DATA, context=context)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data

        project = models.Project.objects.get(id=data["project_id"])
        self.check_permissions(request, 'bulk_create', project)

        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        if not request.user.verified_email:
            return response.BadRequest({
                "_error_message": _("To add members to a project, first you have to verify your email address")
            })

        bulk_memberships = data["bulk_memberships"]
        invitation_extra_text = data.get("invitation_extra_text", None)

        try:
            with advisory_lock("membership-creation-{}".format(project.id)):
                members = services.get_members_from_bulk(bulk_memberships,
                                                         project=project,
                                                         invited_by=request.user,
                                                         invitation_extra_text=invitation_extra_text)
                self._check_if_new_members_can_be_created(project, members)
                services.create_members_in_bulk(members, callback=self.post_save)
                signal_members_added.send(sender=self.__class__,
                                          user=self.request.user,
                                          project=project,
                                          new_members=members)
        except exc.ValidationError as err:
            return response.BadRequest(err.message_dict)

        members_serialized = self.admin_serializer_class(members, many=True)
        return response.Ok(members_serialized.data)

    @detail_route(methods=["POST"])
    def resend_invitation(self, request, **kwargs):
        invitation = self.get_object()

        self.check_permissions(request, 'resend_invitation', invitation.project)
        self.pre_conditions_on_save(invitation)

        services.send_invitation(invitation=invitation)
        return response.NoContent()

    @list_route(methods=["POST"])
    def remove_user_from_all_my_projects(self, request, **kwargs):
        private_only = request.DATA.get('private_only', False)

        user_id = request.DATA.get('user', None)
        if user_id is None:
            raise exc.WrongArguments(_("Invalid user id"))

        user_model = apps.get_model("users", "User")
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist:
            return response.BadRequest(_("The user doesn't exist"))

        memberships = models.Membership.objects.filter(project__owner=request.user, user=user)
        if private_only:
            memberships = memberships.filter(project__is_private=True)

        errors = []
        for membership in memberships:
            if not services.can_user_leave_project(user, membership.project):
                errors.append(membership.project.name)

        if len(errors) > 0:
            error = _("This user can't be removed from the following projects, because that would "
                      "leave them without any active admin: {}.".format(", ".join(errors)))
            return response.BadRequest(error)

        memberships.delete()

        return response.NoContent()

    @list_route(methods=["POST"])
    def remove_invitation_from_all_my_projects(self, request, **kwargs):
        private_only = request.DATA.get('private_only', False)

        email = request.DATA.get('email', None)
        if email is None:
            raise exc.WrongArguments(_("Email is required"))

        memberships = models.Membership.objects.filter(project__owner=request.user, email=email, user__isnull=True)
        if private_only:
            memberships = memberships.filter(project__is_private=True)
        memberships.delete()

        return response.NoContent()

    def pre_delete(self, obj):
        if obj.user is not None and not services.can_user_leave_project(obj.user, obj.project):
            raise exc.BadRequest(_("The project must have an owner and at least one of the users "
                                   "must be an active admin"))

    def pre_save(self, obj):
        if not obj.id:
            self._check_if_new_member_can_be_created(obj)

        obj.invited_by = self.request.user
        obj.user = services.find_invited_user(obj.email, default=obj.user)

        if not obj.token and not obj.user:
            obj.token = str(uuid.uuid1())

        super().pre_save(obj)

    def post_save(self, object, created=False):
        super().post_save(object, created=created)

        if not created:
            return

        # Send email only if a new membership is created
        services.send_invitation(invitation=object)


class InvitationViewSet(ModelListViewSet):
    """
    Only used by front for get invitation by it token.
    """
    queryset = models.Membership.objects.filter(user__isnull=True)
    serializer_class = serializers.MembershipSerializer
    lookup_field = "token"
    permission_classes = (AllowAnyPermission,)

    def list(self, *args, **kwargs):
        raise exc.PermissionDenied(_("You don't have permissions to see that."))
