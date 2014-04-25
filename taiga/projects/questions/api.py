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

from django.contrib.contenttypes.models import ContentType

from rest_framework.permissions import IsAuthenticated

from taiga.base import filters
from taiga.base.api import ModelCrudViewSet
from taiga.base.notifications.api import NotificationSenderMixin
from taiga.projects.permissions import AttachmentPermission
from taiga.projects.serializers import AttachmentSerializer
from taiga.projects.models import Attachment

from . import serializers
from . import models
from . import permissions

import reversion


class QuestionAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.Question)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        super().pre_save(obj)
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.Question)
            obj.owner = self.request.user


class QuestionViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.Question
    serializer_class = serializers.QuestionSerializer
    permission_classes = (IsAuthenticated, permissions.QuestionPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ("project",)
    create_notification_template = "create_question_notification"
    update_notification_template = "update_question_notification"
    destroy_notification_template = "destroy_question_notification"

    def pre_save(self, obj):
        super().pre_save(obj)
        if not obj.id:
            obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA["comment"])
        super().post_save(obj, created)
