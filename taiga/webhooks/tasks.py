# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import hmac
import hashlib
import requests
from requests.exceptions import RequestException

from django.conf import settings

from taiga.base.api.renderers import UnicodeJSONRenderer
from taiga.base.utils import json, urls
from taiga.base.utils.db import get_typename_for_model_instance
from taiga.celery import app

from .serializers import (EpicSerializer, EpicRelatedUserStorySerializer,
                          UserStorySerializer, IssueSerializer, TaskSerializer,
                          WikiPageSerializer, MilestoneSerializer,
                          HistoryEntrySerializer, UserSerializer)

from .models import WebhookLog


def _serialize(obj):
    content_type = get_typename_for_model_instance(obj)
    if content_type == "epics.epic":
        return EpicSerializer(obj).data
    elif content_type == "epics.relateduserstory":
        return EpicRelatedUserStorySerializer(obj).data
    elif content_type == "userstories.userstory":
        return UserStorySerializer(obj).data
    elif content_type == "issues.issue":
        return IssueSerializer(obj).data
    elif content_type == "tasks.task":
        return TaskSerializer(obj).data
    elif content_type == "wiki.wikipage":
        return WikiPageSerializer(obj).data
    elif content_type == "milestones.milestone":
        return MilestoneSerializer(obj).data
    elif content_type == "history.historyentry":
        return HistoryEntrySerializer(obj).data


def _get_type(obj):
    content_type = get_typename_for_model_instance(obj)
    return content_type.split(".")[1]


def _generate_signature(data, key):
    mac = hmac.new(key.encode("utf-8"), msg=data, digestmod=hashlib.sha1)
    return mac.hexdigest()


def _remove_leftover_webhooklogs(webhook_id):
    # Only the last ten webhook logs traces are required
    # so remove the leftover
    ids = (WebhookLog.objects.filter(webhook_id=webhook_id)
               .order_by("-id")
               .values_list('id', flat=True)[10:])
    WebhookLog.objects.filter(id__in=ids).delete()


def _send_request(webhook_id, url, key, data):
    serialized_data = UnicodeJSONRenderer().render(data)
    signature = _generate_signature(serialized_data, key)
    headers = {
        "X-TAIGA-WEBHOOK-SIGNATURE": signature,        # For backward compatibility
        "X-Hub-Signature": "sha1={}".format(signature),
        "Content-Type": "application/json"
    }

    if not settings.WEBHOOKS_ALLOW_PRIVATE_ADDRESS:
        try:
            urls.validate_private_url(url)
        except (urls.IpAddresValueError, urls.HostnameException) as e:
            # Error validating url
            webhook_log = WebhookLog.objects.create(webhook_id=webhook_id,
                                                    url=url,
                                                    status=0,
                                                    request_data=data,
                                                    request_headers=dict(),
                                                    response_data="error-in-request: {}".format(str(e)),
                                                    response_headers={},
                                                    duration=0)
            _remove_leftover_webhooklogs(webhook_id)

            return webhook_log

    request = requests.Request('POST', url, data=serialized_data, headers=headers)
    prepared_request = request.prepare()

    with requests.Session() as session:
        response = None
        try:
            response = session.send(prepared_request, allow_redirects=settings.WEBHOOKS_ALLOW_REDIRECTS)

            if not settings.WEBHOOKS_ALLOW_REDIRECTS and response.status_code in [301, 302, 303, 307, 308]:
                raise RequestException("Redirects are not allowed")

        except RequestException as e:
            # Error sending the webhook
            webhook_log = WebhookLog.objects.create(webhook_id=webhook_id,
                                                    url=url,
                                                    status=response.status_code if response else 0,
                                                    request_data=data,
                                                    request_headers=dict(prepared_request.headers),
                                                    response_data="error-in-request: {}".format(str(e)),
                                                    response_headers={},
                                                    duration=0)
        else:
            # Webhook was sent successfully

            # response.content can be a not valid json so we encapsulate it
            response_data = json.dumps({"content": response.text})
            webhook_log = WebhookLog.objects.create(webhook_id=webhook_id, url=url,
                                                    status=response.status_code,
                                                    request_data=data,
                                                    request_headers=dict(prepared_request.headers),
                                                    response_data=response_data,
                                                    response_headers=dict(response.headers),
                                                    duration=response.elapsed.total_seconds())
        finally:
            _remove_leftover_webhooklogs(webhook_id)

    return webhook_log


@app.task
def create_webhook(webhook_id, url, key, by, date, obj):
    data = {}
    data['action'] = "create"
    data['type'] = _get_type(obj)
    data['by'] = UserSerializer(by).data
    data['date'] = date
    data['data'] = _serialize(obj)

    return _send_request(webhook_id, url, key, data)


@app.task
def delete_webhook(webhook_id, url, key, by, date, obj):
    data = {}
    data['action'] = "delete"
    data['type'] = _get_type(obj)
    data['by'] = UserSerializer(by).data
    data['date'] = date
    data['data'] = _serialize(obj)

    return _send_request(webhook_id, url, key, data)


@app.task
def change_webhook(webhook_id, url, key, by, date, obj, change):
    data = {}
    data['action'] = "change"
    data['type'] = _get_type(obj)
    data['by'] = UserSerializer(by).data
    data['date'] = date
    data['data'] = _serialize(obj)
    data['change'] = _serialize(change)

    return _send_request(webhook_id, url, key, data)


@app.task
def resend_webhook(webhook_id, url, key, data):
    return _send_request(webhook_id, url, key, data)


@app.task
def test_webhook(webhook_id, url, key, by, date):
    data = {}
    data['action'] = "test"
    data['type'] = "test"
    data['by'] = UserSerializer(by).data
    data['date'] = date
    data['data'] = {"test": "test"}
    return _send_request(webhook_id, url, key, data)
