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


#######
# API #
#######

from taiga.projects.notifications import services
from taiga.projects.history.services import take_snapshot
from taiga.projects.history.models import HistoryType


class NotificationSenderMixin(object):
    create_notification_template = None
    update_notification_template = None
    destroy_notification_template = None
    notification_service = services.NotificationService()

    def _get_object_for_snapshot(self, obj):
        return obj

    def _post_save_notification_sender(self, obj, history):
        users = obj.get_watchers_to_notify(history.owner)
        context = {
            "object": obj,
            "changer": history.owner,
            "comment": history.comment,
            "changed_fields": history.values_diff
        }

        if history.type == HistoryType.create:
            self.notification_service.send_notification_email(self.create_notification_template,
                                                              users=users, context=context)
        else:
            self.notification_service.send_notification_email(self.update_notification_template,
                                                              users=users, context=context)

    def post_save(self, obj, created=False):
        super().post_save(obj, created)

        user = self.request.user
        comment = self.request.DATA.get("comment", "")

        obj = self._get_object_for_snapshot(obj)
        history = take_snapshot(obj, comment=comment, user=user)

        if history:
            self._post_save_notification_sender(obj, history)

    def pre_destroy(self, obj):
        obj = self._get_object_for_snapshot(obj)
        users = obj.get_watchers_to_notify(self.request.user)

        context = {
            "object": obj,
            "changer": self.request.user
        }
        self.notification_service.send_notification_email(self.destroy_notification_template,
                                                          users=users, context=context)
    def post_destroy(self, obj):
        pass

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        self.pre_destroy(obj)
        result = super().destroy(request, *args, **kwargs)
        self.post_destroy(obj)

        return result


################
# SERIEALIZERS #
################

from django.db.models.loading import get_model

from rest_framework import serializers


class WatcherValidationSerializerMixin(object):
    def validate_watchers(self, attrs, source):
        values =  set(attrs.get(source, []))
        if values:
            project = None
            if "project" in attrs and attrs["project"]:
                project = attrs["project"]
            elif self.object:
                project = self.object.project

            model_cls = get_model("projects", "Membership")
            if len(values) != model_cls.objects.filter(project=project, user__in=values).count():
                raise serializers.ValidationError("Error, some watcher user is not a member of the project")
        return attrs
