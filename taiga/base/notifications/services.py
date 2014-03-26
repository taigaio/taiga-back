# -*- coding: utf-8 -*-

from djmail import template_mail

import collections


class NotificationService(object):
    def send_notification_email(self, template_method, users=None, context=None):
        if not users:
            return

        if not isinstance(users, collections.Iterable):
            users = (users,)

        mails = template_mail.MagicMailBuilder()
        for user in users:
            email = getattr(mails, template_method)(user, context)
            email.send()
