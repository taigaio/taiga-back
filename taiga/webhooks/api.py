# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.utils import timezone
from django.utils.translation import ugettext as _

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
