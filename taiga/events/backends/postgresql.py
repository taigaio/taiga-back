# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
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
