# -*- coding: utf-8 -*-
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

from django.utils.translation import ugettext_lazy as _

from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelUpdateRetrieveViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base import exceptions as exc
from taiga.base import filters
from taiga.base import response

from taiga.projects.mixins.ordering import BulkUpdateOrderMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.occ.mixins import OCCResourceMixin

from . import models
from . import serializers
from . import validators
from . import permissions
from . import services


######################################################
# Custom Attribute ViewSets
#######################################################

class EpicCustomAttributeViewSet(BulkUpdateOrderMixin, BlockedByProjectMixin, ModelCrudViewSet):
    model = models.EpicCustomAttribute
    serializer_class = serializers.EpicCustomAttributeSerializer
    validator_class = validators.EpicCustomAttributeValidator
    permission_classes = (permissions.EpicCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_epic_custom_attributes"
    bulk_update_perm = "change_epic_custom_attributes"
    bulk_update_order_action = services.bulk_update_epic_custom_attribute_order


class UserStoryCustomAttributeViewSet(BulkUpdateOrderMixin, BlockedByProjectMixin, ModelCrudViewSet):
    model = models.UserStoryCustomAttribute
    serializer_class = serializers.UserStoryCustomAttributeSerializer
    validator_class = validators.UserStoryCustomAttributeValidator
    permission_classes = (permissions.UserStoryCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_userstory_custom_attributes"
    bulk_update_perm = "change_userstory_custom_attributes"
    bulk_update_order_action = services.bulk_update_userstory_custom_attribute_order


class TaskCustomAttributeViewSet(BulkUpdateOrderMixin, BlockedByProjectMixin, ModelCrudViewSet):
    model = models.TaskCustomAttribute
    serializer_class = serializers.TaskCustomAttributeSerializer
    validator_class = validators.TaskCustomAttributeValidator
    permission_classes = (permissions.TaskCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_task_custom_attributes"
    bulk_update_perm = "change_task_custom_attributes"
    bulk_update_order_action = services.bulk_update_task_custom_attribute_order


class IssueCustomAttributeViewSet(BulkUpdateOrderMixin, BlockedByProjectMixin, ModelCrudViewSet):
    model = models.IssueCustomAttribute
    serializer_class = serializers.IssueCustomAttributeSerializer
    validator_class = validators.IssueCustomAttributeValidator
    permission_classes = (permissions.IssueCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_custom_attributes"
    bulk_update_perm = "change_issue_custom_attributes"
    bulk_update_order_action = services.bulk_update_issue_custom_attribute_order


######################################################
# Custom Attributes Values ViewSets
#######################################################

class BaseCustomAttributesValuesViewSet(OCCResourceMixin, HistoryResourceMixin, WatchedResourceMixin,
                                        BlockedByProjectMixin, ModelUpdateRetrieveViewSet):
    def get_object_for_snapshot(self, obj):
        return getattr(obj, self.content_object)


class EpicCustomAttributesValuesViewSet(BaseCustomAttributesValuesViewSet):
    model = models.EpicCustomAttributesValues
    serializer_class = serializers.EpicCustomAttributesValuesSerializer
    validator_class = validators.EpicCustomAttributesValuesValidator
    permission_classes = (permissions.EpicCustomAttributesValuesPermission,)
    lookup_field = "epic_id"
    content_object = "epic"

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related("epic", "epic__project")
        return qs


class UserStoryCustomAttributesValuesViewSet(BaseCustomAttributesValuesViewSet):
    model = models.UserStoryCustomAttributesValues
    serializer_class = serializers.UserStoryCustomAttributesValuesSerializer
    validator_class = validators.UserStoryCustomAttributesValuesValidator
    permission_classes = (permissions.UserStoryCustomAttributesValuesPermission,)
    lookup_field = "user_story_id"
    content_object = "user_story"

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related("user_story", "user_story__project")
        return qs


class TaskCustomAttributesValuesViewSet(BaseCustomAttributesValuesViewSet):
    model = models.TaskCustomAttributesValues
    serializer_class = serializers.TaskCustomAttributesValuesSerializer
    validator_class = validators.TaskCustomAttributesValuesValidator
    permission_classes = (permissions.TaskCustomAttributesValuesPermission,)
    lookup_field = "task_id"
    content_object = "task"

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related("task", "task__project")
        return qs


class IssueCustomAttributesValuesViewSet(BaseCustomAttributesValuesViewSet):
    model = models.IssueCustomAttributesValues
    serializer_class = serializers.IssueCustomAttributesValuesSerializer
    validator_class = validators.IssueCustomAttributesValuesValidator
    permission_classes = (permissions.IssueCustomAttributesValuesPermission,)
    lookup_field = "issue_id"
    content_object = "issue"

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related("issue", "issue__project")
        return qs
