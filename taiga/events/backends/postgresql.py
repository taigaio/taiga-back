from django.db import transaction
from django.db import connection

from . import base


class EventsPushBackend(base.BaseEventsPushBackend):
    @transaction.atomic
    def emit_event(self, message:str, *, channel:str="events"):
        sql = "NOTIFY {channel}, %s".format(channel=channel)
        cursor = connection.cursor()
        cursor.execute(sql, [message])
        cursor.close()
