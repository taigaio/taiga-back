# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
