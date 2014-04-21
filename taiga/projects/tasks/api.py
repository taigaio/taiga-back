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

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.permissions import has_project_perm
from taiga.base.api import ModelCrudViewSet
from taiga.base.notifications.api import NotificationSenderMixin
from taiga.projects.permissions import AttachmentPermission
from taiga.projects.serializers import AttachmentSerializer
from taiga.projects.models import Attachment, Project
from taiga.projects.userstories.models import UserStory

from . import models
from . import permissions
from . import serializers

import reversion


class TaskAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Task)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Task)
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PermissionDenied(_("You don't have permissions for add "
                                         "attachments to this task."))


class TaskViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Task
    serializer_class = serializers.TaskSerializer
    permission_classes = (IsAuthenticated, permissions.TaskPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["user_story", "milestone", "project"]

    create_notification_template = "create_task_notification"
    update_notification_template = "update_task_notification"
    destroy_notification_template = "destroy_task_notification"

    def pre_save(self, obj):
        if obj.user_story:
            obj.milestone = obj.user_story.milestone
        if not obj.id:
            obj.owner = self.request.user
        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this task."))

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this task."))

        if obj.user_story and obj.user_story.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this task."))

        if obj.status and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this task."))

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super().post_save(obj, created)

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        bulk_tasks = request.DATA.get('bulkTasks', None)
        if bulk_tasks is None:
            raise exc.BadRequest(_('bulkTasks parameter is mandatory'))

        project_id = request.DATA.get('projectId', None)
        if project_id is None:
            raise exc.BadRequest(_('projectId parameter is mandatory'))

        us_id = request.DATA.get('usId', None)
        if us_id is None:
            raise exc.BadRequest(_('usId parameter is mandatory'))

        project = get_object_or_404(Project, id=project_id)
        us = get_object_or_404(UserStory, id=us_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'add_task'):
            raise exc.PermissionDenied(_("You don't have permisions to create tasks."))

        items = filter(lambda s: len(s) > 0,
                    map(lambda s: s.strip(), bulk_tasks.split("\n")))

        tasks = []
        for item in items:
            obj = models.Task.objects.create(subject=item, project=project,
                                             user_story=us, owner=request.user,
                                             status=project.default_task_status)
            tasks.append(obj)
            self._post_save_notification_sender(obj, True)

        tasks_serialized = self.serializer_class(tasks, many=True)
        return Response(data=tasks_serialized.data)
