# -*- coding: utf-8 -*-

from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext
from django.template.loader import render_to_string

from greenmine.base import signals
from greenmine.base.utils.auth import set_token
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

## TODO: Remove me when base.notifications is finished
##
#@receiver(signals.mail_milestone_created)
#def mail_milestone_created(sender, milestone, user, **kwargs):
#    participants = milestone.project.all_participants()
#
#    emails_list = []
#    subject = ugettext("Greenmine: sprint created")
#    for person in participants:
#        template = render_to_string("email/milestone.created.html", {
#            "person": person,
#            "current_host": settings.HOST,
#            "milestone": milestone,
#            "user": user,
#        })
#
#        emails_list.append([subject, template, [person.email]])
#
#    send_bulk_mail.delay(emails_list)
#
#
#@receiver(signals.mail_userstory_created)
#def mail_userstory_created(sender, us, user, **kwargs):
#    participants = us.milestone.project.all_participants()
#
#    emails_list = []
#    subject = ugettext("Greenmine: user story created")
#
#    for person in participants:
#        template = render_to_string("email/userstory.created.html", {
#            "person": person,
#            "current_host": settings.HOST,
#            "us": us,
#            "user": user,
#        })
#
#        emails_list.append([subject, template, [person.email]])
#
#    send_bulk_mail.delay(emails_list)
#
#
#@receiver(signals.mail_task_created)
#def mail_task_created(sender, task, user, **kwargs):
#    participants = task.us.milestone.project.all_participants()
#
#    emails_list = []
#    subject = ugettext("Greenmine: task created")
#
#    for person in participants:
#        template = render_to_string("email/task.created.html", {
#            "person": person,
#            "current_host": settings.HOST,
#            "task": task,
#            "user": user,
#        })
#
#        emails_list.append([subject, template, [person.email]])
#
#    send_bulk_mail.delay(emails_list)
#
#
#@receiver(signals.mail_task_assigned)
#def mail_task_assigned(sender, task, user, **kwargs):
#    template = render_to_string("email/task.assigned.html", {
#        "person": task.assigned_to,
#        "task": task,
#        "user": user,
#        "current_host": settings.HOST,
#    })
#
#    subject = ugettext("Greenmine: task assigned")
#    send_mail.delay(subject, template, [task.assigned_to.email])
