# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import json
import logging

from amqp import Connection as AmqpConnection
from amqp.exceptions import AccessRefused
from amqp.basic_message import Message as AmqpMessage
from urllib.parse import urlparse

from . import base

log = logging.getLogger("tagia.events")


def _make_rabbitmq_connection(url):
    parse_result = urlparse(url)

    # Parse host & user/password
    try:
        (authdata, host) = parse_result.netloc.split("@")
    except Exception as e:
        raise RuntimeError("Invalid url") from e

    try:
        (user, password) = authdata.split(":")
    except Exception:
        (user, password) = ("guest", "guest")

    vhost = parse_result.path
    return AmqpConnection(host=host, userid=user,
                          password=password, virtual_host=vhost[1:])


class EventsPushBackend(base.BaseEventsPushBackend):
    def __init__(self, url):
        self.url = url

    def emit_event(self, message:str, *, routing_key:str, channel:str="events"):
        connection = _make_rabbitmq_connection(self.url)
        try:
            connection.connect()
        except ConnectionRefusedError:
            err_msg = "EventsPushBackend: Unable to connect with RabbitMQ (connection refused) at {}".format(
                                                                                                     self.url)
            log.error(err_msg, exc_info=True)
        except AccessRefused:
            err_msg = "EventsPushBackend: Unable to connect with RabbitMQ (access refused) at {}".format(
                                                                                                 self.url)
            log.error(err_msg, exc_info=True)
        else:
            try:
                message = AmqpMessage(message)
                rchannel = connection.channel()

                rchannel.exchange_declare(exchange=channel, type="topic", auto_delete=True)
                rchannel.basic_publish(message, routing_key=routing_key, exchange=channel)
                rchannel.close()
            except Exception:
                log.error("EventsPushBackend: Unhandled exception", exc_info=True)
            finally:
                connection.close()
