# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from taiga.base.db.models.fields import JSONField
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from taiga.projects.models import Project


class Timeline(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="content_type_timelines", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    namespace = models.CharField(max_length=250, default="default", db_index=True)
    event_type = models.CharField(max_length=250, db_index=True)
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)
    data = JSONField()
    data_content_type = models.ForeignKey(ContentType, related_name="data_timelines", on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['namespace', '-created']),
            models.Index(fields=['content_type', 'object_id', '-created']),
        ]


# Register all implementations
from .timeline_implementations import *

# Register all signals
from .signals import *
