# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils import timezone
from django.utils.translation import gettext as _

from taiga.base import filters
from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin

from taiga.base.decorators import detail_route

from . import models
from . import serializers
from . import validators
from . import permissions
from . import tasks


class WebhookViewSet(BlockedByProjectMixin, ModelCrudViewSet):
    model = models.Webhook
    serializer_class = serializers.WebhookSerializer
    validator_class = validators.WebhookValidator
    permission_classes = (permissions.WebhookPermission,)
    filter_backends = (filters.IsProjectAdminFilterBackend,)
    filter_fields = ("project",)

    @detail_route(methods=["POST"])
    def test(self, request, pk=None):
        webhook = self.get_object()
        self.check_permissions(request, 'test', webhook)
        self.pre_conditions_blocked(webhook)

        webhooklog = tasks.test_webhook(webhook.id, webhook.url, webhook.key, request.user, timezone.now())
        log = serializers.WebhookLogSerializer(webhooklog)

        return response.Ok(log.data)


class WebhookLogViewSet(ModelListViewSet):
    model = models.WebhookLog
    serializer_class = serializers.WebhookLogSerializer
    permission_classes = (permissions.WebhookLogPermission,)
    filter_backends = (filters.IsProjectAdminFromWebhookLogFilterBackend,)
    filter_fields = ("webhook",)

    @detail_route(methods=["POST"])
    def resend(self, request, pk=None):
        webhooklog = self.get_object()
        self.check_permissions(request, 'resend', webhooklog)
        webhook = webhooklog.webhook
        if webhook.project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        webhooklog = tasks.resend_webhook(webhook.id, webhook.url, webhook.key,
                                          webhooklog.request_data)

        log = serializers.WebhookLogSerializer(webhooklog)

        return response.Ok(log.data)
