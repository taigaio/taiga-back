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

from . import services


class NotificationSenderMixin(object):
    create_notification_template = None
    update_notification_template = None
    destroy_notification_template = None
    notification_service = services.NotificationService()

    def _post_save_notification_sender(self, obj, created=False):
        users = obj.get_watchers_to_notify(self.request.user)
        comment = self.request.DATA.get("comment", None)
        context = {'changer': self.request.user, "comment": comment, 'object': obj}

        if created:
            self.notification_service.send_notification_email(self.create_notification_template,
                                                              users=users, context=context)
        else:
            context["changed_fields"] = obj.get_changed_fields_list(self.request.DATA)
            self.notification_service.send_notification_email(self.update_notification_template,
                                                              users=users, context=context)

    def post_save(self, obj, created=False):
        super().post_save(obj, created)
        self._post_save_notification_sender(obj, created)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        users = obj.get_watchers_to_notify(self.request.user)

        context = {'changer': self.request.user, 'object': obj}
        self.notification_service.send_notification_email(self.destroy_notification_template,
                                                          users=users, context=context)

        return super().destroy(request, *args, **kwargs)
