# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.projects import services
from taiga.users.serializers import UserBasicInfoSerializer


class CachedUsersSerializerMixin(serializers.LightSerializer):
    def to_value(self, instance):
        self._serialized_users = {}
        return super().to_value(instance)

    def get_user_extra_info(self, user):
        if user is None:
            return None

        serialized_user = self._serialized_users.get(user.id, None)
        if serialized_user is None:
            serialized_user = UserBasicInfoSerializer(user).data
            self._serialized_users[user.id] = serialized_user

        return serialized_user


class OwnerExtraInfoSerializerMixin(CachedUsersSerializerMixin):
    owner = Field(attr="owner_id")
    owner_extra_info = MethodField()

    def get_owner_extra_info(self, obj):
        return self.get_user_extra_info(obj.owner)


class AssignedToExtraInfoSerializerMixin(CachedUsersSerializerMixin):
    assigned_to = Field(attr="assigned_to_id")
    assigned_to_extra_info = MethodField()

    def get_assigned_to_extra_info(self, obj):
        return self.get_user_extra_info(obj.assigned_to)


class StatusExtraInfoSerializerMixin(serializers.LightSerializer):
    status = Field(attr="status_id")
    status_extra_info = MethodField()

    def to_value(self, instance):
        self._serialized_status = {}
        return super().to_value(instance)

    def get_status_extra_info(self, obj):
        if obj.status_id is None:
            return None

        serialized_status = self._serialized_status.get(obj.status_id, None)
        if serialized_status is None:
            serialized_status = {
                "name": _(obj.status.name),
                "color": obj.status.color,
                "is_closed": obj.status.is_closed
            }
            self._serialized_status[obj.status_id] = serialized_status

        return serialized_status


class ProjectExtraInfoSerializerMixin(serializers.LightSerializer):
    project = Field(attr="project_id")
    project_extra_info = MethodField()

    def to_value(self, instance):
        self._serialized_project = {}
        return super().to_value(instance)

    def get_project_extra_info(self, obj):
        if obj.project_id is None:
            return None

        serialized_project = self._serialized_project.get(obj.project_id, None)
        if serialized_project is None:
            serialized_project = {
                "name": obj.project.name,
                "slug": obj.project.slug,
                "logo_small_url": services.get_logo_small_thumbnail_url(obj.project),
                "id": obj.project_id
            }
            self._serialized_project[obj.project_id] = serialized_project

        return serialized_project
