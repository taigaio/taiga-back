# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.base.fields import Field, DateTimeField, MethodField
from taiga.users.gravatar import get_user_gravatar_id
from taiga.users.models import get_user_model_safe
from taiga.users.services import get_user_photo_url, get_user_big_photo_url

from . import models


class NotifyPolicySerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField("get_project_name")

    class Meta:
        model = models.NotifyPolicy
        fields = ('id', 'project', 'project_name', 'notify_level',
                  'live_notify_level', 'web_notify_level')

    def get_project_name(self, obj):
        return obj.project.name


class WatcherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', required=False)

    class Meta:
        model = get_user_model_safe()
        fields = ('id', 'username', 'full_name')


class WebNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebNotification
        fields = ('id', 'event_type', 'user', 'data', 'created', 'read')


class ProjectSerializer(serializers.LightSerializer):
    id = Field()
    slug = Field()
    name = Field()


class ObjectSerializer(serializers.LightSerializer):
    id = Field()
    ref = MethodField()
    subject = MethodField()
    content_type = MethodField()

    def get_ref(self, obj):
        return obj.ref if hasattr(obj, 'ref') else None

    def get_subject(self, obj):
        return obj.subject if hasattr(obj, 'subject') else None

    def get_content_type(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return content_type.model if content_type else None


class UserSerializer(serializers.LightSerializer):
    id = Field()
    name = MethodField()
    photo = MethodField()
    big_photo = MethodField()
    gravatar_id = MethodField()
    username = Field()
    is_profile_visible = MethodField()
    date_joined = DateTimeField()

    def get_name(self, obj):
        return obj.get_full_name()

    def get_photo(self, obj):
        return get_user_photo_url(obj)

    def get_big_photo(self, obj):
        return get_user_big_photo_url(obj)

    def get_gravatar_id(self, obj):
        return get_user_gravatar_id(obj)

    def get_is_profile_visible(self, obj):
        return obj.is_active and not obj.is_system


class NotificationDataSerializer(serializers.LightDictSerializer):
    project = ProjectSerializer()
    user = UserSerializer()


class ObjectNotificationSerializer(NotificationDataSerializer):
    obj = ObjectSerializer()
