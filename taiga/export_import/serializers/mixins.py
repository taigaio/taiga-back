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

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.projects.notifications import services as notifications_services
from taiga.projects.history import services as history_service

from .fields import (UserRelatedField, HistoryUserField, HistoryDiffField,
                     JsonField, HistoryValuesField, CommentField, FileField)


class HistoryExportSerializer(serializers.ModelSerializer):
    user = HistoryUserField()
    diff = HistoryDiffField(required=False)
    snapshot = JsonField(required=False)
    values = HistoryValuesField(required=False)
    comment = CommentField(required=False)
    delete_comment_date = serializers.DateTimeField(required=False)
    delete_comment_user = HistoryUserField(required=False)

    class Meta:
        model = history_models.HistoryEntry
        exclude = ("id", "comment_html", "key")


class HistoryExportSerializerMixin(serializers.ModelSerializer):
    history = serializers.SerializerMethodField("get_history")

    def get_history(self, obj):
        history_qs = history_service.get_history_queryset_by_model_instance(obj,
            types=(history_models.HistoryType.change, history_models.HistoryType.create,))

        return HistoryExportSerializer(history_qs, many=True).data


class AttachmentExportSerializer(serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    attached_file = FileField()
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = attachments_models.Attachment
        exclude = ('id', 'content_type', 'object_id', 'project')


class AttachmentExportSerializerMixin(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField("get_attachments")

    def get_attachments(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        attachments_qs = attachments_models.Attachment.objects.filter(object_id=obj.pk,
                                                                      content_type=content_type)
        return AttachmentExportSerializer(attachments_qs, many=True).data


class CustomAttributesValuesExportSerializerMixin(serializers.ModelSerializer):
    custom_attributes_values = serializers.SerializerMethodField("get_custom_attributes_values")

    def custom_attributes_queryset(self, project):
        raise NotImplementedError()

    def get_custom_attributes_values(self, obj):
        def _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values):
            ret = {}
            for attr in custom_attributes:
                value = values.get(str(attr["id"]), None)
                if value is not  None:
                    ret[attr["name"]] = value

            return ret

        try:
            values =  obj.custom_attributes_values.attributes_values
            custom_attributes = self.custom_attributes_queryset(obj.project)

            return _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values)
        except ObjectDoesNotExist:
            return None


class WatcheableObjectModelSerializerMixin(serializers.ModelSerializer):
    watchers = UserRelatedField(many=True, required=False)

    def __init__(self, *args, **kwargs):
        self._watchers_field = self.base_fields.pop("watchers", None)
        super(WatcheableObjectModelSerializerMixin, self).__init__(*args, **kwargs)

    """
    watchers is not a field from the model so we need to do some magic to make it work like a normal field
    It's supposed to be represented as an email list but internally it's treated like notifications.Watched instances
    """

    def restore_object(self, attrs, instance=None):
        watcher_field = self.fields.pop("watchers", None)
        instance = super(WatcheableObjectModelSerializerMixin, self).restore_object(attrs, instance)
        self._watchers = self.init_data.get("watchers", [])
        return instance

    def save_watchers(self):
        new_watcher_emails = set(self._watchers)
        old_watcher_emails = set(self.object.get_watchers().values_list("email", flat=True))
        adding_watcher_emails = list(new_watcher_emails.difference(old_watcher_emails))
        removing_watcher_emails = list(old_watcher_emails.difference(new_watcher_emails))

        User = get_user_model()
        adding_users = User.objects.filter(email__in=adding_watcher_emails)
        removing_users = User.objects.filter(email__in=removing_watcher_emails)

        for user in adding_users:
            notifications_services.add_watcher(self.object, user)

        for user in removing_users:
            notifications_services.remove_watcher(self.object, user)

        self.object.watchers = [user.email for user in self.object.get_watchers()]

    def to_native(self, obj):
        ret = super(WatcheableObjectModelSerializerMixin, self).to_native(obj)
        ret["watchers"] = [user.email for user in obj.get_watchers()]
        return ret
