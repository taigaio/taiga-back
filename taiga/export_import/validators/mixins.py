# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.projects.notifications import services as notifications_services
from taiga.projects.history import services as history_service

from .fields import (UserRelatedField, HistoryUserField, HistoryDiffField,
                     JSONField, HistorySnapshotField,
                     HistoryValuesField, CommentField, FileField)


class HistoryExportValidator(validators.ModelValidator):
    user = HistoryUserField()
    diff = HistoryDiffField(required=False)
    snapshot = HistorySnapshotField(required=False)
    values = HistoryValuesField(required=False)
    comment = CommentField(required=False)
    delete_comment_date = serializers.DateTimeField(required=False)
    delete_comment_user = HistoryUserField(required=False)

    class Meta:
        model = history_models.HistoryEntry
        exclude = ("id", "comment_html", "key", "project")

    def restore_object(self, attrs, instance=None):
        snapshot = attrs["snapshot"]
        statuses = self.context.get("statuses", {})
        if "status" in snapshot:
            status_id = statuses.get(snapshot["status"], None)
            attrs["snapshot"]["status"] = status_id

        instance = super(HistoryExportValidator, self).restore_object(attrs, instance)
        return instance

class AttachmentExportValidator(validators.ModelValidator):
    owner = UserRelatedField(required=False)
    attached_file = FileField()
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = attachments_models.Attachment
        exclude = ('id', 'content_type', 'object_id', 'project')


class WatcheableObjectModelValidatorMixin(validators.ModelValidator):
    watchers = UserRelatedField(many=True, required=False)

    def __init__(self, *args, **kwargs):
        self._watchers_field = self.base_fields.pop("watchers", None)
        super(WatcheableObjectModelValidatorMixin, self).__init__(*args, **kwargs)

    """
    watchers is not a field from the model so we need to do some magic to make it work like a normal field
    It's supposed to be represented as an email list but internally it's treated like notifications.Watched instances
    """

    def restore_object(self, attrs, instance=None):
        self.fields.pop("watchers", None)
        instance = super(WatcheableObjectModelValidatorMixin, self).restore_object(attrs, instance)
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
        ret = super(WatcheableObjectModelValidatorMixin, self).to_native(obj)
        ret["watchers"] = [user.email for user in obj.get_watchers()]
        return ret
