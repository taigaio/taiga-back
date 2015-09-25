from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taiga.projects.attachments.models import Attachment


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):
        for attachment in Attachment.objects.all():
            attachment.save()
