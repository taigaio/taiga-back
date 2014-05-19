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

from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from taiga.base.api import ModelCrudViewSet
from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.projects.mixins.notifications import NotificationSenderMixin
from taiga.projects.history.services import take_snapshot

from . import permissions
from . import serializers
from . import models


class BaseAttachmentViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Attachment
    serializer_class = serializers.AttachmentSerializer
    permission_classes = (IsAuthenticated, permissions.AttachmentPermission,)

    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    content_type = None

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return get_object_or_404(ContentType, app_label=app_name, model=model)

    def get_queryset(self):
        ct = self.get_content_type()
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = self.get_content_type()
            obj.owner = self.request.user

        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PermissionDenied(_("You don't have permissions for "
                                         "add attachments to this user story"))

    def _get_object_for_snapshot(self, obj):
        return obj.content_object

    def pre_destroy(self, obj):
        pass

    def post_destroy(self, obj):
        user = self.request.user
        comment = self.request.DATA.get("comment", "")

        obj = self._get_object_for_snapshot(obj)
        history = take_snapshot(obj, comment=comment, user=user)

        if history:
            self._post_save_notification_sender(obj, history)


class UserStoryAttachmentViewSet(BaseAttachmentViewSet):
    content_type = "userstories.userstory"
    create_notification_template = "create_userstory_notification"
    update_notification_template = "update_userstory_notification"
    destroy_notification_template = "destroy_userstory_notification"


class IssueAttachmentViewSet(BaseAttachmentViewSet):
    content_type = "issues.issue"
    create_notification_template = "create_issue_notification"
    update_notification_template = "update_issue_notification"
    destroy_notification_template = "destroy_issue_notification"


class TaskAttachmentViewSet(BaseAttachmentViewSet):
    content_type = "tasks.task"
    create_notification_template = "create_task_notification"
    update_notification_template = "update_task_notification"
    destroy_notification_template = "destroy_task_notification"


class WikiAttachmentViewSet(BaseAttachmentViewSet):
    content_type = "wiki.wikipage"
    create_notification_template = "create_wiki_notification"
    update_notification_template = "update_wiki_notification"
    destroy_notification_template = "destroy_wiki_notification"
