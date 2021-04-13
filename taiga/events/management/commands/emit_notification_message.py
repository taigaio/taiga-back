# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from taiga.events.events import emit_event

class Command(BaseCommand):
    help = 'Send a notification message to the current users'

    def add_arguments(self, parser):
        parser.add_argument("title",  help="The title of the message.")
        parser.add_argument("description",  help="The description of the message.")

    def handle(self, **options):
        data = {
            "title": options["title"],
            "desc": options["description"],
        }
        routing_key = "notifications"
        emit_event(data, routing_key, on_commit=False)
