# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
