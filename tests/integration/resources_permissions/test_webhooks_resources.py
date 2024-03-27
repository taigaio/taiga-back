# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.urls import reverse

from taiga.base.utils import json
from taiga.projects import choices as project_choices
from taiga.webhooks.serializers import WebhookSerializer
from taiga.webhooks.models import Webhook

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

from unittest import mock

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()

    m.project1 = f.ProjectFactory(is_private=True,
                                  anon_permissions=[],
                                  public_permissions=[],
                                  owner=m.project_owner)
    m.project2 = f.ProjectFactory(is_private=True,
                                  anon_permissions=[],
                                  public_permissions=[],
                                  owner=m.project_owner)
    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF)

    f.MembershipFactory(project=m.project1,
                        user=m.project_owner,
                        is_admin=True)
    f.MembershipFactory(project=m.blocked_project,
                        user=m.project_owner,
                        is_admin=True)

    m.webhook1 = f.WebhookFactory(project=m.project1)
    m.webhooklog1 = f.WebhookLogFactory(webhook=m.webhook1)
    m.webhook2 = f.WebhookFactory(project=m.project2)
    m.webhooklog2 = f.WebhookLogFactory(webhook=m.webhook2)
    m.blocked_webhook = f.WebhookFactory(project=m.blocked_project)
    m.blocked_webhooklog = f.WebhookLogFactory(webhook=m.blocked_webhook)

    return m


def test_webhook_retrieve(client, data):
    url1 = reverse('webhooks-detail', kwargs={"pk": data.webhook1.pk})
    url2 = reverse('webhooks-detail', kwargs={"pk": data.webhook2.pk})
    blocked_url = reverse('webhooks-detail', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', url1, None, users)
    assert results == [401, 403, 200]
    results = helper_test_http_method(client, 'get', url2, None, users)
    assert results == [401, 403, 403]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 200]


def test_webhook_update(client, data):
    url1 = reverse('webhooks-detail', kwargs={"pk": data.webhook1.pk})
    url2 = reverse('webhooks-detail', kwargs={"pk": data.webhook2.pk})
    blocked_url = reverse('webhooks-detail', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    webhook_data = WebhookSerializer(data.webhook1).data
    webhook_data["key"] = "test"
    webhook_data = json.dumps(webhook_data)
    results = helper_test_http_method(client, 'put', url1, webhook_data, users)
    assert results == [401, 403, 200]

    webhook_data = WebhookSerializer(data.webhook2).data
    webhook_data["key"] = "test"
    webhook_data = json.dumps(webhook_data)
    results = helper_test_http_method(client, 'put', url2, webhook_data, users)
    assert results == [401, 403, 403]

    webhook_data = WebhookSerializer(data.blocked_webhook).data
    webhook_data["key"] = "test"
    webhook_data = json.dumps(webhook_data)
    results = helper_test_http_method(client, 'put', blocked_url, webhook_data, users)
    assert results == [401, 403, 451]


def test_webhook_delete(client, data):
    url1 = reverse('webhooks-detail', kwargs={"pk": data.webhook1.pk})
    url2 = reverse('webhooks-detail', kwargs={"pk": data.webhook2.pk})
    blocked_url = reverse('webhooks-detail', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'delete', url1, None, users)
    assert results == [401, 403, 204]
    results = helper_test_http_method(client, 'delete', url2, None, users)
    assert results == [401, 403, 403]
    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [401, 403, 451]


def test_webhook_list(client, data):
    url = reverse('webhooks-list')

    response = client.get(url)
    webhooks_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooks_data) == 0
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    webhooks_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooks_data) == 0
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    webhooks_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooks_data) == 2
    assert response.status_code == 200


def test_webhook_create(client, data):
    url = reverse('webhooks-list')

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    create_data = json.dumps({
        "name": "Test",
        "url": "http://test.com",
        "key": "test",
        "project": data.project1.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: Webhook.objects.all().delete())
    assert results == [401, 403, 201]

    create_data = json.dumps({
        "name": "Test",
        "url": "http://test.com",
        "key": "test",
        "project": data.project2.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: Webhook.objects.all().delete())
    assert results == [401, 403, 403]

    create_data = json.dumps({
        "name": "Test",
        "url": "http://test.com",
        "key": "test",
        "project": data.blocked_project.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: Webhook.objects.all().delete())
    assert results == [401, 403, 451]


def test_webhook_patch(client, data):
    url1 = reverse('webhooks-detail', kwargs={"pk": data.webhook1.pk})
    url2 = reverse('webhooks-detail', kwargs={"pk": data.webhook2.pk})
    blocked_url = reverse('webhooks-detail', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    patch_data = json.dumps({"key": "test"})
    results = helper_test_http_method(client, 'patch', url1, patch_data, users)
    assert results == [401, 403, 200]

    patch_data = json.dumps({"key": "test"})
    results = helper_test_http_method(client, 'patch', url2, patch_data, users)
    assert results == [401, 403, 403]

    patch_data = json.dumps({"key": "test"})
    results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
    assert results == [401, 403, 451]


def test_webhook_action_test(client, data):
    url1 = reverse('webhooks-test', kwargs={"pk": data.webhook1.pk})
    url2 = reverse('webhooks-test', kwargs={"pk": data.webhook2.pk})
    blocked_url = reverse('webhooks-test', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    with mock.patch('taiga.webhooks.tasks._send_request') as _send_request_mock:
        _send_request_mock.return_value = data.webhooklog1
        results = helper_test_http_method(client, 'post', url1, None, users)
        assert results == [401, 404, 200]
        assert _send_request_mock.called is True

    with mock.patch('taiga.webhooks.tasks._send_request') as _send_request_mock:
        _send_request_mock.return_value = data.webhooklog1
        results = helper_test_http_method(client, 'post', url2, None, users)
        assert results == [401, 404, 404]
        assert _send_request_mock.called is False

    with mock.patch('taiga.webhooks.tasks._send_request') as _send_request_mock:
        _send_request_mock.return_value = data.webhooklog1
        results = helper_test_http_method(client, 'post', blocked_url, None, users)
        assert results == [401, 404, 451]
        assert _send_request_mock.called is False


def test_webhooklogs_list(client, data):
    url = reverse('webhooklogs-list')

    response = client.get(url)
    webhooklogs_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooklogs_data) == 0
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    webhooklogs_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooklogs_data) == 0
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    webhooklogs_data = json.loads(response.content.decode('utf-8'))
    assert len(webhooklogs_data) == 2
    assert response.status_code == 200


def test_webhooklogs_retrieve(client, data):
    url1 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog1.pk})
    url2 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog2.pk})
    blocked_url = reverse('webhooks-detail', kwargs={"pk": data.blocked_webhook.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', url1, None, users)
    assert results == [401, 403, 200]

    results = helper_test_http_method(client, 'get', url2, None, users)
    assert results == [401, 403, 403]

    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 200]


def test_webhooklogs_create(client, data):
    url1 = reverse('webhooklogs-list')
    url2 = reverse('webhooklogs-list')
    blocked_url = reverse('webhooklogs-list')

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', url1, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'post', url2, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [405, 405, 405]


def test_webhooklogs_delete(client, data):
    url1 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog1.pk})
    url2 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog2.pk})
    blocked_url = reverse('webhooklogs-detail', kwargs={"pk": data.blocked_webhooklog.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'delete', url1, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'delete', url2, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [405, 405, 405]


def test_webhooklogs_update(client, data):
    url1 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog1.pk})
    url2 = reverse('webhooklogs-detail', kwargs={"pk": data.webhooklog2.pk})
    blocked_url = reverse('webhooklogs-detail', kwargs={"pk": data.blocked_webhooklog.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'put', url1, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'put', url2, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'put', blocked_url, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'patch', url1, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'patch', url2, None, users)
    assert results == [405, 405, 405]

    results = helper_test_http_method(client, 'patch', blocked_url, None, users)
    assert results == [405, 405, 405]


def test_webhooklogs_action_resend(client, data):
    url1 = reverse('webhooklogs-resend', kwargs={"pk": data.webhooklog1.pk})
    url2 = reverse('webhooklogs-resend', kwargs={"pk": data.webhooklog2.pk})
    blocked_url = reverse('webhooklogs-resend', kwargs={"pk": data.blocked_webhooklog.pk})

    users = [
        None,
        data.registered_user,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', url1, None, users)
    assert results == [401, 404, 200]

    results = helper_test_http_method(client, 'post', url2, None, users)
    assert results == [401, 404, 404]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [401, 404, 451]
