# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from django.contrib.contenttypes.fields import GenericForeignKey

from taiga.projects.models import Project

class Timeline(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="content_type_timelines")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    namespace = models.CharField(max_length=250, default="default", db_index=True)
    event_type = models.CharField(max_length=250, db_index=True)
    project = models.ForeignKey(Project, null=True)
    data = JsonField()
    data_content_type = models.ForeignKey(ContentType, related_name="data_timelines")
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        index_together = [('content_type', 'object_id', 'namespace'), ]


# Register all implementations
from .timeline_implementations import *

# Register all signals
from .signals import *
