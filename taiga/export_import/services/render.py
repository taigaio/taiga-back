# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# This makes all code that import services works and
# is not the baddest practice ;)

import gc

from taiga.base.utils import json
from taiga.base.fields import MethodField
from taiga.timeline.service import get_project_timeline
from taiga.base.api.fields import get_component

from .. import serializers


def render_project(project, outfile, chunk_size=8190):
    serializer = serializers.ProjectExportSerializer(project)
    outfile.write(b'{\n')

    first_field = True
    for field_name in serializer._field_map.keys():
        # Avoid writing "," in the last element
        if not first_field:
            outfile.write(b",\n")
        else:
            first_field = False

        field = serializer._field_map.get(field_name)
        # field.initialize(parent=serializer, field_name=field_name)

        # These four "special" fields hava attachments so we use them in a special way
        if field_name in ["wiki_pages", "user_stories", "tasks", "issues", "epics"]:
            value = get_component(project, field_name)
            if field_name != "wiki_pages":
                value = value.select_related('owner', 'status',
                                             'project', 'assigned_to',
                                             'custom_attributes_values')

            if field_name in ["user_stories", "tasks", "issues"]:
                value = value.select_related('milestone')

            if field_name == "issues":
                value = value.select_related('severity', 'priority', 'type')
            value = value.prefetch_related('history_entry', 'attachments')

            outfile.write('"{}": [\n'.format(field_name).encode())

            first_item = True
            for item in value.iterator():
                # Avoid writing "," in the last element
                if not first_item:
                    outfile.write(b",\n")
                else:
                    first_item = False

                field.many = False
                dumped_value = json.dumps(field.to_value(item))
                outfile.write(dumped_value.encode())
                outfile.flush()
            gc.collect()
            outfile.write(b']')
        else:
            if isinstance(field, MethodField):
                value = field.as_getter(field_name, serializers.ProjectExportSerializer)(serializer, project)
            else:
                attr = getattr(project, field_name)
                value = field.to_value(attr)
            outfile.write('"{}": {}'.format(field_name, json.dumps(value)).encode())

    # Generate the timeline
    outfile.write(b',\n"timeline": [\n')
    first_timeline = True
    for timeline_item in get_project_timeline(project).iterator():
        # Avoid writing "," in the last element
        if not first_timeline:
            outfile.write(b",\n")
        else:
            first_timeline = False

        dumped_value = json.dumps(serializers.TimelineExportSerializer(timeline_item).data)
        outfile.write(dumped_value.encode())

    outfile.write(b']}\n')
