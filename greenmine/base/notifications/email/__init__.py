# -*- coding: utf-8 -*-

from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from greenmine.base.notifications.models import watched_changed


@receiver(watched_changed)
def send_mail_when_watched_changed(sender, **kwargs):
    changed_attributes = kwargs.get('changed_attributes')
    watchers_to_notify = sender.get_watchers_to_notify()

    print 'Cambiado', sender
    print 'Atributos', changed_attributes
    print 'Notificar a', watchers_to_notify

