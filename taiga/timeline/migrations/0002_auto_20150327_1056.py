# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from django.core.exceptions import ObjectDoesNotExist
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

import django_pgjson.fields
import django.utils.timezone


timelime_objects = []
created = None

def custom_add_to_object_timeline(obj:object, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    global created
    global timelime_objects
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    timelime_objects.append(Timeline(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        project=instance.project,
        data=impl(instance, extra_data=extra_data),
        data_content_type = ContentType.objects.get_for_model(instance.__class__),
        created = created,
    ))


def generate_timeline(apps, schema_editor):
    global created
    global timelime_objects
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

        Timeline.objects.bulk_create(timelime_objects, batch_size=10000)
        timelime_objects = []

        for historyEntry in HistoryEntry.objects.order_by("created_at").iterator():
            print("History entry:", historyEntry.created_at)
            try:
                created = historyEntry.created_at
                on_new_history_entry(None, historyEntry, None)
            except ObjectDoesNotExist as e:
                print("Ignoring")

        Timeline.objects.bulk_create(timelime_objects, batch_size=10000)

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0019_auto_20150311_0821'),
        ('contenttypes', '0001_initial'),
        ('timeline', '0001_initial'),
        ('users', '0010_auto_20150414_0936'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Timeline',
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('namespace', models.SlugField(default='default')),
                ('event_type', models.SlugField()),
                ('project', models.ForeignKey(to='projects.Project')),
                ('data', django_pgjson.fields.JsonField()),
                ('data_content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='data_timelines')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='content_type_timelines')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='timeline',
            index_together=set([('content_type', 'object_id', 'namespace')]),
        ),
        migrations.RunPython(generate_timeline),
    ]
