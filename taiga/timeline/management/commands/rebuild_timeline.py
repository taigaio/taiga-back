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

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Model

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

timeline_objects = []
created = None

def custom_add_to_object_timeline(obj:object, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    global created
    global timeline_objects
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    timeline_objects.append(Timeline(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        project=instance.project,
        data=impl(instance, extra_data=extra_data),
        data_content_type = ContentType.objects.get_for_model(instance.__class__),
        created = created,
    ))

def bulk_create():
    global timeline_objects
    if len(timeline_objects) > 10000:
        Timeline.objects.bulk_create(timeline_objects, batch_size=10000)
        timeline_objects = []

def generate_timeline():
    global created
    with patch('taiga.timeline.service._add_to_object_timeline', new=custom_add_to_object_timeline):
        # Projects api wasn't a HistoryResourceMixin so we can't interate on the HistoryEntries in this case
        for project in Project.objects.order_by("created_date").iterator():
            created = project.created_date
            print("Project:", created)
            extra_data = {
                "values_diff": {},
                "user": extract_user_info(project.owner),
            }
            _push_to_timelines(project, project.owner, project, "create", extra_data=extra_data)
            bulk_create()

        for historyEntry in HistoryEntry.objects.order_by("created_at").iterator():
            print("History entry:", historyEntry.created_at)
            try:
                created = historyEntry.created_at
                on_new_history_entry(None, historyEntry, None)
            except ObjectDoesNotExist as e:
                print("Ignoring")

            bulk_create()


class Command(BaseCommand):
    def handle(self, *args, **options):
        Timeline.objects.all().delete()
        generate_timeline()
