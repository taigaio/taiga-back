# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
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

from taiga.base.api import ModelCrudViewSet
from taiga.base import filters
from taiga.projects.mixins.ordering import BulkUpdateOrderMixin

from . import models
from . import serializers
from . import permissions
from . import services


class UserStoryCustomAttributeViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.UserStoryCustomAttribute
    serializer_class = serializers.UserStoryCustomAttributeSerializer
    permission_classes = (permissions.UserStoryCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_userstory_custom_attributes"
    bulk_update_perm = "change_userstory_custom_attributes"
    bulk_update_order_action = services.bulk_update_userstory_custom_attribute_order


class TaskCustomAttributeViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.TaskCustomAttribute
    serializer_class = serializers.TaskCustomAttributeSerializer
    permission_classes = (permissions.TaskCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_task_custom_attributes"
    bulk_update_perm = "change_task_custom_attributes"
    bulk_update_order_action = services.bulk_update_task_custom_attribute_order


class IssueCustomAttributeViewSet(ModelCrudViewSet, BulkUpdateOrderMixin):
    model = models.IssueCustomAttribute
    serializer_class = serializers.IssueCustomAttributeSerializer
    permission_classes = (permissions.IssueCustomAttributePermission,)
    filter_backends = (filters.CanViewProjectFilterBackend,)
    filter_fields = ("project",)
    bulk_update_param = "bulk_issue_custom_attributes"
    bulk_update_perm = "change_issue_custom_attributes"
    bulk_update_order_action = services.bulk_update_issue_custom_attribute_order
