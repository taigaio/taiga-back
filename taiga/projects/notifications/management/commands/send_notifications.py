# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand

from taiga.projects.notifications.services import send_bulk_email

class Command(BaseCommand):

    def handle(self, *args, **options):
        send_bulk_email()
