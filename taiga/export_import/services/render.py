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

# This makes all code that import services works and
# is not the baddest practice ;)

import base64
import gc
import os

from django.core.files.storage import default_storage

from taiga.base.utils import json
from taiga.timeline.service import get_project_timeline
from taiga.base.api.fields import get_component

from .. import serializers


def render_project(project, outfile, chunk_size = 8190):
    serializer = serializers.ProjectExportSerializer(project)
    outfile.write(b'{\n')

    first_field = True
    for field_name in serializer.fields.keys():
        # Avoid writing "," in the last element
        if not first_field:
            outfile.write(b",\n")
        else:
            first_field = False

        field = serializer.fields.get(field_name)
        field.initialize(parent=serializer, field_name=field_name)

        # These four "special" fields hava attachments so we use them in a special way
        if field_name in ["wiki_pages", "user_stories", "tasks", "issues"]:
            value = get_component(project, field_name)
            if field_name != "wiki_pages":
                value = value.select_related('owner', 'status', 'milestone', 'project', 'assigned_to', 'custom_attributes_values')
            if field_name == "issues":
                value = value.select_related('severity', 'priority', 'type')
            value = value.prefetch_related('history_entry', 'attachments')

            outfile.write('"{}": [\n'.format(field_name).encode())

            attachments_field = field.fields.pop("attachments", None)
            if attachments_field:
                attachments_field.initialize(parent=field, field_name="attachments")

            first_item = True
            for item in value.iterator():
                # Avoid writing "," in the last element
                if not first_item:
                    outfile.write(b",\n")
                else:
                    first_item = False


                dumped_value = json.dumps(field.to_native(item))
                writing_value = dumped_value[:-1]+ ',\n    "attachments": [\n'
                outfile.write(writing_value.encode())

                first_attachment = True
                for attachment in item.attachments.iterator():
                    # Avoid writing "," in the last element
                    if not first_attachment:
                        outfile.write(b",\n")
                    else:
                        first_attachment = False

                    # Write all the data expect the serialized file
                    attachment_serializer = serializers.AttachmentExportSerializer(instance=attachment)
                    attached_file_serializer = attachment_serializer.fields.pop("attached_file")
                    dumped_value = json.dumps(attachment_serializer.data)
                    dumped_value = dumped_value[:-1] + ',\n        "attached_file":{\n            "data":"'
                    outfile.write(dumped_value.encode())

                    # We write the attached_files by chunks so the memory used is not increased
                    attachment_file = attachment.attached_file
                    if default_storage.exists(attachment_file.name):
                        with default_storage.open(attachment_file.name) as f:
                            while True:
                                bin_data = f.read(chunk_size)
                                if not bin_data:
                                    break

                                b64_data = base64.b64encode(bin_data)
                                outfile.write(b64_data)

                    outfile.write('", \n            "name":"{}"}}\n}}'.format(
                                        os.path.basename(attachment_file.name)).encode())

                outfile.write(b']}')
                outfile.flush()
            gc.collect()
            outfile.write(b']')
        else:
            value = field.field_to_native(project, field_name)
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

