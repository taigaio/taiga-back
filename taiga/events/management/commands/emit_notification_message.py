# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
