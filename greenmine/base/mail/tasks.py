# -*- coding: utf-8 -*-

from celery import task

from django.core import mail


@task(name='send-mail')
def send_mail(subject, body, to):
    email_message = mail.EmailMessage(body=body, subject=subject, to=to)
    email_message.content_subtype = "html"
    email_message.send()


@task(name='send-bulk-mail')
def send_bulk_mail(emails):
    emessages = [mail.EmailMessage(body=body, subject=subject, to=to)
                 for subject, body, to in emails]

    for msg in emessages:
        msg.content_subtype = "html"

    connection = mail.get_connection()
    connection.send_messages(emessages)
