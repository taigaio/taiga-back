# -*- coding: utf-8 -*-

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
            changed_fields = obj.get_changed_fields_list(self.request.DATA)

            if changed_fields:
                context["changed_fields"] = changed_fields
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
