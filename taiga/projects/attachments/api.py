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

import os
import hashlib
import mimetypes
mimetypes.init()

from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.conf import settings
from django import http

from taiga.base.api import ModelCrudViewSet
from taiga.base.api import generics
from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.users.models import User

from taiga.projects.notifications import WatchedResourceMixin
from taiga.projects.history import HistoryResourceMixin


from . import permissions
from . import serializers
from . import models


class BaseAttachmentViewSet(HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    model = models.Attachment
    serializer_class = serializers.AttachmentSerializer
    filter_fields = ["project", "object_id"]

    content_type = None

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return get_object_or_404(ContentType, app_label=app_name, model=model)

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = self.get_content_type()
            obj.owner = self.request.user

        super().pre_save(obj)

    def post_delete(self, obj):
        # NOTE: When destroy an attachment, the content_object change
        #       after and not before
        self.persist_history_snapshot(obj, delete=True)
        super().pre_delete(obj)

    def get_object_for_snapshot(self, obj):
        return obj.content_object


class UserStoryAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.UserStoryAttachmentPermission,)
    filter_backends = (filters.CanViewUserStoryAttachmentFilterBackend,)
    content_type = "userstories.userstory"
    create_notification_template = "create_userstory_notification"
    update_notification_template = "update_userstory_notification"
    destroy_notification_template = "destroy_userstory_notification"


class IssueAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.IssueAttachmentPermission,)
    filter_backends = (filters.CanViewIssueAttachmentFilterBackend,)
    content_type = "issues.issue"
    create_notification_template = "create_issue_notification"
    update_notification_template = "update_issue_notification"
    destroy_notification_template = "destroy_issue_notification"


class TaskAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.TaskAttachmentPermission,)
    filter_backends = (filters.CanViewTaskAttachmentFilterBackend,)
    content_type = "tasks.task"
    create_notification_template = "create_task_notification"
    update_notification_template = "update_task_notification"
    destroy_notification_template = "destroy_task_notification"


class WikiAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.WikiAttachmentPermission,)
    filter_backends = (filters.CanViewWikiAttachmentFilterBackend,)
    content_type = "wiki.wikipage"
    create_notification_template = "create_wiki_notification"
    update_notification_template = "update_wiki_notification"
    destroy_notification_template = "destroy_wiki_notification"


class RawAttachmentView(generics.RetrieveAPIView):
    queryset = models.Attachment.objects.all()
    permission_classes = (permissions.RawAttachmentPermission,)

    def _serve_attachment(self, attachment):
        if settings.IN_DEVELOPMENT_SERVER:
            return http.HttpResponseRedirect(attachment.url)

        name = attachment.name
        response = http.HttpResponse()
        response['X-Accel-Redirect'] = "/{filepath}".format(filepath=name)
        response['Content-Disposition'] = 'attachment;filename={filename}'.format(
            filename=os.path.basename(name))
        response['Content-Type'] = mimetypes.guess_type(name)

        return response

    def check_permissions(self, request, action='retrieve', obj=None):
        self.object = self.get_object()
        user_id = self.request.QUERY_PARAMS.get('user', None)
        token = self.request.QUERY_PARAMS.get('token', None)

        if token and user_id:
            token_src = "{}-{}-{}".format(settings.ATTACHMENTS_TOKEN_SALT, user_id, self.object.id)
            if token == hashlib.sha1(token_src.encode("utf-8")).hexdigest():
                request.user = get_object_or_404(User, pk=user_id)

        return super().check_permissions(request, action, self.object)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.check_permissions(request, 'retrieve', self.object)
        return self._serve_attachment(self.object.attached_file)
