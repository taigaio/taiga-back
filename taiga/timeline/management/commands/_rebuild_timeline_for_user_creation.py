# -*- coding: utf-8 -*-
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

# Examples:
# python manage.py rebuild_timeline_for_user_creation --settings=settings.local_timeline

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.test.utils import override_settings

from taiga.timeline.service import _get_impl_key_from_model,
from taiga.timeline.service import _timeline_impl_map,
from taiga.timeline.service import extract_user_info)
from taiga.timeline.models import Timeline
from taiga.timeline.signals import _push_to_timelines

from unittest.mock import patch

import gc


class BulkCreator(object):
    def __init__(self):
        self.timeline_objects = []
        self.created = None

    def create_element(self, element):
        self.timeline_objects.append(element)
        if len(self.timeline_objects) > 1000:
            self.flush()

    def flush(self):
        Timeline.objects.bulk_create(self.timeline_objects, batch_size=1000)
        del self.timeline_objects
        self.timeline_objects = []
        gc.collect()

bulk_creator = BulkCreator()


def custom_add_to_object_timeline(obj:object, instance:object, event_type:str, created_datetime:object,
                                  namespace:str="default", extra_data:dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    bulk_creator.create_element(Timeline(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        project=None,
        data=impl(instance, extra_data=extra_data),
        data_content_type = ContentType.objects.get_for_model(instance.__class__),
        created=created_datetime,
    ))


def generate_timeline():
    with patch('taiga.timeline.service._add_to_object_timeline', new=custom_add_to_object_timeline):
        # Users api wasn't a HistoryResourceMixin so we can't interate on the HistoryEntries in this case
        users = get_user_model().objects.order_by("date_joined")
        for user in users.iterator():
            print("User:", user.date_joined)
            extra_data = {
                "values_diff": {},
                "user": extract_user_info(user),
            }
            _push_to_timelines(None, user, user, "create", user.date_joined, extra_data=extra_data)
            del extra_data

    bulk_creator.flush()


class Command(BaseCommand):
    help = 'Regenerate project timeline'

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        generate_timeline()
