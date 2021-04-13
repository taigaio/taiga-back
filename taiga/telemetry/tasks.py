# -*- coding: utf-8 -*-
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
