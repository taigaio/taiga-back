# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import codecs
import uuid
import gzip
import logging


from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.db.transaction import atomic
from django.db.models import signals
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from taiga.base.utils import json
from taiga.base.decorators import detail_route, list_route
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.api.mixins import CreateModelMixin
from taiga.base.api.viewsets import GenericViewSet
from taiga.projects import utils as project_utils
from taiga.projects.models import Project, Membership
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.serializers import ProjectSerializer
from taiga.users import services as users_services

from . import exceptions as err
from . import mixins
from . import permissions
from . import validators
from . import serializers
from . import services
from . import tasks
from . import throttling

from taiga.base.api.utils import get_object_or_error

logger = logging.getLogger(__name__)

class ProjectExporterViewSet(mixins.ImportThrottlingPolicyMixin, GenericViewSet):
    model = Project
    permission_classes = (permissions.ImportExportPermission, )

    def retrieve(self, request, pk, *args, **kwargs):
        throttle = throttling.ImportDumpModeRateThrottle()

        if not throttle.allow_request(request, self):
            self.throttled(request, throttle.wait())

        project = get_object_or_error(self.get_queryset(), request.user, pk=pk)
        self.check_permissions(request, 'export_project', project)

        dump_format = request.QUERY_PARAMS.get("dump_format", "plain")

        if settings.CELERY_ENABLED:
            task = tasks.dump_project.delay(request.user, project, dump_format)
            tasks.delete_project_dump.apply_async((project.pk, project.slug, task.id, dump_format),
                                                  countdown=settings.EXPORTS_TTL)
            return response.Accepted({"export_id": task.id})

        if dump_format == "gzip":
            path = "exports/{}/{}-{}.json.gz".format(project.pk, project.slug, uuid.uuid4().hex)
            with default_storage.open(path, mode="wb") as outfile:
                services.render_project(project, gzip.GzipFile(fileobj=outfile, mode="wb"))
        else:
            path = "exports/{}/{}-{}.json".format(project.pk, project.slug, uuid.uuid4().hex)
            with default_storage.open(path, mode="wb") as outfile:
                services.render_project(project, outfile)

        response_data = {
            "url": default_storage.url(path)
        }
        return response.Ok(response_data)


class ProjectImporterViewSet(mixins.ImportThrottlingPolicyMixin, CreateModelMixin, GenericViewSet):
    model = Project
    permission_classes = (permissions.ImportExportPermission, )

    @method_decorator(atomic)
    def create(self, request, *args, **kwargs):
        self.check_permissions(request, 'import_project', None)

        data = request.DATA.copy()
        data['owner'] = data.get('owner', request.user.email)

        # Validate if the project can be imported
        is_private = data.get('is_private', False)
        memberships = [m["email"] for m in data.get("memberships", []) if m.get("email", None)]
        (enough_slots, error_message, total_memberships) = services.has_available_slot_for_new_project(
            self.request.user,
            is_private,
            memberships
        )
        if not enough_slots:
            raise exc.NotEnoughSlotsForProject(is_private, total_memberships, error_message)

        # Create Project
        project_serialized = services.store.store_project(data)

        if not project_serialized:
            raise exc.BadRequest(services.store.get_errors())

        # Create roles
        roles_serialized = None
        if "roles" in data:
            roles_serialized = services.store.store_roles(project_serialized.object, data)

        if not roles_serialized:
            raise exc.BadRequest(_("We needed at least one role"))

        # Create memberships
        if "memberships" in data:
            services.store.store_memberships(project_serialized.object, data)

        try:
            owner_membership = project_serialized.object.memberships.get(user=project_serialized.object.owner)
            owner_membership.is_admin = True
            owner_membership.save()
        except Membership.DoesNotExist:
            Membership.objects.create(
                project=project_serialized.object,
                email=project_serialized.object.owner.email,
                user=project_serialized.object.owner,
                role=project_serialized.object.roles.all().first(),
                is_admin=True
            )

        # Create project values choices
        if "points" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "points", validators.PointsExportValidator)
        if "issue_types" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "issue_types",
                                                           validators.IssueTypeExportValidator)
        if "issue_statuses" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "issue_statuses",
                                                           validators.IssueStatusExportValidator,)
        if "issue_duedates" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "issue_duedates",
                                                           validators.IssueDueDateExportValidator,)
        if "us_statuses" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "us_statuses",
                                                           validators.UserStoryStatusExportValidator,)
        if "us_duedates" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "us_duedates",
                                                           validators.UserStoryDueDateExportValidator,)
        if "task_statuses" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "task_statuses",
                                                           validators.TaskStatusExportValidator)
        if "task_duedates" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "task_duedates",
                                                           validators.TaskDueDateExportValidator)
        if "priorities" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "priorities",
                                                           validators.PriorityExportValidator)
        if "severities" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "severities",
                                                           validators.SeverityExportValidator)
        if "swimlanes" in data:
            services.store.store_project_attributes_values(project_serialized.object, data,
                                                           "swimlanes",
                                                           validators.SwimlaneExportValidator)

        if ("points" in data or "issues_types" in data or
                "issues_statuses" in data or "us_statuses" in data or
                "task_statuses" in data or "priorities" in data or
                "severities" in data):
            services.store.store_default_project_attributes_values(project_serialized.object, data)

        # Created custom attributes
        if "userstorycustomattributes" in data:
            services.store.store_custom_attributes(project_serialized.object, data,
                                                   "userstorycustomattributes",
                                                   validators.UserStoryCustomAttributeExportValidator)

        if "taskcustomattributes" in data:
            services.store.store_custom_attributes(project_serialized.object, data,
                                                   "taskcustomattributes",
                                                   validators.TaskCustomAttributeExportValidator)

        if "issuecustomattributes" in data:
            services.store.store_custom_attributes(project_serialized.object, data,
                                                   "issuecustomattributes",
                                                   validators.IssueCustomAttributeExportValidator)

        # Is there any error?
        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        # Importer process is OK
        response_data = serializers.ProjectExportSerializer(project_serialized.object).data
        response_data['id'] = project_serialized.object.id
        headers = self.get_success_headers(response_data)
        return response.Created(response_data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def milestone(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        milestone = services.store.store_milestone(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.MilestoneExportSerializer(milestone.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def us(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        us = services.store.store_user_story(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.UserStoryExportSerializer(us.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def task(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        signals.pre_save.disconnect(sender=Task,
                                    dispatch_uid="set_finished_date_when_edit_task")

        task = services.store.store_task(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.TaskExportSerializer(task.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def issue(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        signals.pre_save.disconnect(sender=Issue,
                                    dispatch_uid="set_finished_date_when_edit_issue")

        issue = services.store.store_issue(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.IssueExportSerializer(issue.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def wiki_page(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        wiki_page = services.store.store_wiki_page(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.WikiPageExportSerializer(wiki_page.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @detail_route(methods=['post'])
    @method_decorator(atomic)
    def wiki_link(self, request, *args, **kwargs):
        project = self.get_object_or_none()
        self.check_permissions(request, 'import_item', project)

        wiki_link = services.store.store_wiki_link(project, request.DATA.copy())

        errors = services.store.get_errors()
        if errors:
            raise exc.BadRequest(errors)

        data = serializers.WikiLinkExportSerializer(wiki_link.object).data
        headers = self.get_success_headers(data)
        return response.Created(data, headers=headers)

    @list_route(methods=["POST"])
    @method_decorator(atomic)
    def load_dump(self, request):
        throttle = throttling.ImportDumpModeRateThrottle()

        if not throttle.allow_request(request, self):
            self.throttled(request, throttle.wait())

        self.check_permissions(request, "load_dump", None)

        dump = request.FILES.get('dump', None)

        if not dump:
            raise exc.WrongArguments(_("Needed dump file"))

        if dump.content_type == "application/gzip":
            dump = gzip.GzipFile(fileobj=dump)

        reader = codecs.getreader("utf-8")

        try:
            dump = json.load(reader(dump))
            
        except Exception:
            raise exc.WrongArguments(_("Invalid dump format"))

        if not isinstance(dump, dict):
            logger.error("trying a load_dump with a different format than dict: {0}, from user {1}".format(dump, request.user))
            raise exc.WrongArguments(_("Invalid dump format"))

        slug = dump.get('slug', None)
        if slug is not None and Project.objects.filter(slug=slug).exists():
            del dump['slug']

        user = request.user
        dump['owner'] = user.email

        # Validate if the project can be imported
        is_private = dump.get("is_private", False)
        memberships = [m["email"] for m in dump.get("memberships", []) if m.get("email", None)]
        (enough_slots, error_message, total_memberships) = services.has_available_slot_for_new_project(
            user,
            is_private,
            memberships
        )
        if not enough_slots:
            raise exc.NotEnoughSlotsForProject(is_private, total_memberships, error_message)

        # Async mode
        if settings.CELERY_ENABLED:
            task = tasks.load_project_dump.delay(user, dump)
            return response.Accepted({"import_id": task.id})

        # Sync mode
        try:
            project = services.store_project_from_dict(dump, request.user)
        except err.TaigaImportError as e:
            # On Error
            ## remove project
            if e.project:
                e.project.delete_related_content()
                e.project.delete()

            return response.BadRequest({"error": e.message, "details": e.errors})
        else:
            # On Success
            project_from_qs = project_utils.attach_extra_info(Project.objects.all()).get(id=project.id)
            response_data = ProjectSerializer(project_from_qs).data

            return response.Created(response_data)
