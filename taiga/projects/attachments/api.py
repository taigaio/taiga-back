# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

import os.path as path
import mimetypes
mimetypes.init()

from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.api import ModelCrudViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_error

from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.history.mixins import HistoryResourceMixin

from . import permissions
from . import serializers
from . import validators
from . import models


class BaseAttachmentViewSet(HistoryResourceMixin, WatchedResourceMixin,
                            BlockedByProjectMixin, ModelCrudViewSet):

    model = models.Attachment
    serializer_class = serializers.AttachmentSerializer
    validator_class = validators.AttachmentValidator
    filter_fields = ["project", "object_id"]

    content_type = None

    def update(self, *args, **kwargs):
        partial = kwargs.get("partial", False)
        if not partial:
            raise exc.NotSupported(_("Partial updates are not supported"))
        return super().update(*args, **kwargs)

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return get_object_or_error(ContentType, self.request.user, app_label=app_name, model=model)

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = self.get_content_type()
            obj.owner = self.request.user
            obj.size = obj.attached_file.size
            obj.name = path.basename(obj.attached_file.name)

        if obj.content_object is None:
            raise exc.WrongArguments(_("Object id issue doesn't exist"))

        if obj.project_id != obj.content_object.project_id:
            raise exc.WrongArguments(_("Project ID does not match between object and project"))

        super().pre_save(obj)

    def post_delete(self, obj):
        # NOTE: When destroy an attachment, the content_object change
        #       after and not before
        self.persist_history_snapshot(obj, delete=True)
        super().post_delete(obj)

    def get_object_for_snapshot(self, obj):
        return obj.content_object


class EpicAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.EpicAttachmentPermission,)
    filter_backends = (filters.CanViewEpicAttachmentFilterBackend,)
    content_type = "epics.epic"


class UserStoryAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.UserStoryAttachmentPermission,)
    filter_backends = (filters.CanViewUserStoryAttachmentFilterBackend,)
    content_type = "userstories.userstory"


class IssueAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.IssueAttachmentPermission,)
    filter_backends = (filters.CanViewIssueAttachmentFilterBackend,)
    content_type = "issues.issue"


class TaskAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.TaskAttachmentPermission,)
    filter_backends = (filters.CanViewTaskAttachmentFilterBackend,)
    content_type = "tasks.task"


class WikiAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (permissions.WikiAttachmentPermission,)
    filter_backends = (filters.CanViewWikiAttachmentFilterBackend,)
    content_type = "wiki.wikipage"
