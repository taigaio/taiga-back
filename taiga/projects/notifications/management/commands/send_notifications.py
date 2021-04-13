# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from taiga.projects.notifications.services import send_bulk_email

class Command(BaseCommand):

    def handle(self, *args, **options):
        send_bulk_email()
