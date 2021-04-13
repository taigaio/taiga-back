# -*- coding: utf-8 -*-
from django.db import transaction
from django.db import connection

from . import base


class EventsPushBackend(base.BaseEventsPushBackend):
    @transaction.atomic
    def emit_event(self, message:str, *, routing_key:str, channel:str="events"):
        routing_key = routing_key.replace(".", "__")
        channel = "{channel}_{routing_key}".format(channel=channel,
                                                   routing_key=routing_key)
        sql = "NOTIFY {channel}, %s".format(channel=channel)
        cursor = connection.cursor()
        cursor.execute(sql, [message])
        cursor.close()
