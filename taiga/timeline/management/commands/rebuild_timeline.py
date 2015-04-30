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

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db import reset_queries

from taiga.projects.models import Project
from taiga.projects.history import services as history_services
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.models import HistoryEntry
from taiga.timeline.models import Timeline
from taiga.timeline.service import (_add_to_object_timeline, _get_impl_key_from_model,
    _timeline_impl_map, extract_user_info)
from taiga.timeline.signals import on_new_history_entry, _push_to_timelines
from taiga.users.models import User

from unittest.mock import patch
from django.contrib.contenttypes.models import ContentType

import gc

class BulkCreator(object):
    def __init__(self):
        self.timeline_objects = []
        self.created = None

    def createElement(self, element):
        self.timeline_objects.append(element)
        if len(self.timeline_objects) > 1000:
            Timeline.objects.bulk_create(self.timeline_objects, batch_size=1000)
            del self.timeline_objects
            self.timeline_objects = []
            gc.collect()

bulk_creator = BulkCreator()


def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    queryset = queryset.order_by('pk')
    pk = queryset[0].pk
    last_pk = queryset.order_by('-pk')[0].pk
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()

def custom_add_to_object_timeline(obj:object, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    bulk_creator.createElement(Timeline(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        project=instance.project,
        data=impl(instance, extra_data=extra_data),
        data_content_type = ContentType.objects.get_for_model(instance.__class__),
        created = bulk_creator.created,
    ))


def generate_timeline():
    with patch('taiga.timeline.service._add_to_object_timeline', new=custom_add_to_object_timeline):
        # Projects api wasn't a HistoryResourceMixin so we can't interate on the HistoryEntries in this case
        for project in queryset_iterator(Project.objects.order_by("created_date")):
            bulk_creator.created = project.created_date
            print("Project:", bulk_creator.created)
            extra_data = {
                "values_diff": {},
                "user": extract_user_info(project.owner),
            }
            _push_to_timelines(project, project.owner, project, "create", extra_data=extra_data)
            del extra_data

        for historyEntry in queryset_iterator(HistoryEntry.objects.order_by("created_at")):
            print("History entry:", historyEntry.created_at)
            try:
                bulk_creator.created = historyEntry.created_at
                on_new_history_entry(None, historyEntry, None)
            except ObjectDoesNotExist as e:
                print("Ignoring")


class Command(BaseCommand):
    def handle(self, *args, **options):
        debug_enabled = settings.DEBUG
        if debug_enabled:
            print("Please, execute this script only with DEBUG mode disabled (DEBUG=False)")
            return

        Timeline.objects.all().delete()
        generate_timeline()
