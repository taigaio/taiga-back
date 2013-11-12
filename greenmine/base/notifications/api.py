# -*- coding: utf-8 -*-

from djmail import template_mail


class NotificationSenderMixin(object):
    create_notification_template = None
    update_notification_template = None
    destroy_notification_template = None

    def _send_notification_email(self, template_method, users=None, context=None):
        mails = template_mail.MagicMailBuilder()
        for user in users:
            email = getattr(mails, template_method)(user, context)
            email.send()

    def post_save(self, obj, created=False):
        super().post_save(obj, created)

        users = obj.get_watchers_to_notify(self.request.user)
        comment = self.request.DATA.get("comment", None)
        context = {'changer': self.request.user, "comment": comment, 'object': obj}

        if created:
            self._send_notification_email(self.create_notification_template,
                                          users=users, context=context)
        else:
            changed_fields = obj.get_changed_fields_list(self.request.DATA)

            if changed_fields:
                context["changed_fields"] = changed_fields
                self._send_notification_email(self.update_notification_template,
                                              users=users, context=context)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        users = obj.get_watchers_to_notify(self.request.user)

        context = {'changer': self.request.user, 'object': obj}
        self._send_notification_email(self.destroy_notification_template,
                                      users=users, context=context)

        return super().destroy(request, *args, **kwargs)
