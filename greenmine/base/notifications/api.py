# -*- coding: utf-8 -*-i

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
        users = obj.get_watchers_to_notify(self.request.user)
        context = {
            "changer": self.request.user,
            "object": obj
        }

        if created:
            self._send_notification_email(self.create_notification_template, users=users, context=context)
        else:
            context["changed_fields_dict"] = obj.get_changed_fields_dict(self.request.DATA)
            self._send_notification_email(self.update_notification_template, users=users, context=context)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        users = obj.get_watchers_to_notify(self.request.user)
        context = {
            'changer': self.request.user,
            'object': obj
        }
        self._send_notification_email(self.destroy_notification_template, users=users, context=context)

        return super(NotificationSenderMixin, self).destroy(request, *args, **kwargs)
