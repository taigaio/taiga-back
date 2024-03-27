# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taiga.projects.attachments.models import Attachment

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        total = rest = Attachment.objects.all().count()

        for attachment in Attachment.objects.all().order_by("id"):
            attachment.save()

            rest -= 1
            logger.debug("[{} / {} remaining] - Generate sha1 for attach {}".format(rest, total, attachment.id))
