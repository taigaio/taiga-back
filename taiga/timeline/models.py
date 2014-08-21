# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django_pgjson.fields import JsonField
from django.utils import timezone

from django.core.exceptions import ValidationError

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey


class Timeline(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    namespace = models.SlugField(default="default")
    event_type = models.SlugField()
    data = JsonField()
    created = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.id:
            raise ValidationError("Not modify allowed for timeline entries")
        return super().save(*args, **kwargs)

    class Meta:
        index_together = [('content_type', 'object_id', 'namespace'), ]


# Register all implementations
from .timeline_implementations import *

# Register all signals
from .signals import *
