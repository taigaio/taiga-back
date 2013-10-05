# -*- coding: utf-8 -*-

from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext
from django.template.loader import render_to_string

from greenmine.base import signals
from greenmine.base.users.utils import set_token
from greenmine.base.mail.tasks import send_mail, send_bulk_mail


@receiver(signals.mail_new_user)
def mail_new_user(sender, user, **kwargs):
    template = render_to_string("email/new.user.html", {
        "user": user,
        "token": set_token(user),
        'current_host': settings.HOST,
    })

    subject = ugettext("Greenmine: wellcome!")
    send_mail.delay(subject, template, [user.email])


@receiver(signals.mail_recovery_password)
def mail_recovery_password(sender, user, **kwargs):
    template = render_to_string("email/forgot.password.html", {
        "user": user,
        "token": set_token(user),
        "current_host": settings.HOST,
    })
    subject = ugettext("Greenmine: password recovery.")
    send_mail.delay(subject, template, [user.email])
