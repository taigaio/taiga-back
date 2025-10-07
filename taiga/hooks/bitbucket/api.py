# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from taiga.base import exceptions as exc
from taiga.projects.models import Project
from taiga.hooks.api import BaseWebhookApiViewSet

from . import event_hooks

from netaddr import all_matching_cidrs
from netaddr.core import AddrFormatError
from urllib.parse import parse_qs
from ipware.ip import get_client_ip


class BitBucketViewSet(BaseWebhookApiViewSet):
    event_hook_classes = {
        "repo:push": event_hooks.PushEventHook,
        "issue:created": event_hooks.IssuesEventHook,
        "issue:comment_created": event_hooks.IssueCommentEventHook,
    }

    def _validate_signature(self, project, request):
        secret_key = request.GET.get("key", None)

        if secret_key is None:
            return False

        if not hasattr(project, "modules_config"):
            return False

        if project.modules_config.config is None:
            return False

        project_secret = project.modules_config.config.get("bitbucket", {}).get("secret", "")
        if not project_secret:
            return False

        bitbucket_config = project.modules_config.config.get("bitbucket", {})
        valid_origin_ips = bitbucket_config.get("valid_origin_ips",
                                                settings.BITBUCKET_VALID_ORIGIN_IPS)
        origin_ip, _routable = get_client_ip(request)
        matching_origin_ip = True

        if valid_origin_ips:
            try:
                matching_origin_ip = len(all_matching_cidrs(origin_ip,valid_origin_ips)) > 0

            except(AddrFormatError, ValueError):
                matching_origin_ip = False

        if not matching_origin_ip:
            return False

        return project_secret == secret_key

    def _get_event_name(self, request):
        return request.headers.get('x-event-key', None)
