# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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
import rudder_analytics

import taiga
from taiga.celery import app
from taiga.telemetry import services



@app.task
def send_telemetry():
    rudder_analytics.write_key = settings.RUDDER_WRITE_KEY
    rudder_analytics.data_plane_url = settings.DATA_PLANE_URL

    instance = services.get_or_create_instance_info()
    event = 'Daily telemetry'

    properties = {
        **services.generate_platform_data(),
        'version': taiga.__version__,
        'running_since': instance.created_at,
        'instance_src': settings.INSTANCE_TYPE
    }

    rudder_analytics.track(
        user_id=instance.instance_id,
        event=event,
        properties=properties
    )
