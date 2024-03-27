# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
    instance_host = f'{ settings.SITES["front"]["scheme"] }://{ settings.SITES["front"]["domain"] }{ settings.FORCE_SCRIPT_NAME }'
    event = 'Daily telemetry'

    properties = {
        **services.generate_platform_data(),
        'version': taiga.__version__,
        'running_since': instance.created_at,
        'instance_src': settings.INSTANCE_TYPE,
        'instance_host': instance_host
    }

    rudder_analytics.track(
        user_id=instance.instance_id,
        event=event,
        properties=properties
    )
