# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.hooks.api import BaseWebhookApiViewSet

from . import event_hooks

import hmac
import hashlib


class GogsViewSet(BaseWebhookApiViewSet):
    event_hook_classes = {
        "push": event_hooks.PushEventHook
    }

    def _validate_signature(self, project, request):
        if not hasattr(project, "modules_config"):
            return False

        if project.modules_config.config is None:
            return False

        secret = project.modules_config.config.get("gogs", {}).get("secret", None)
        if secret is None:
            return False

        signature = request.headers.get("x-gogs-signature", None)
        if not signature:  # Old format signature support (before 0.11 version)
            payload = self._get_payload(request)
            return payload.get('secret', None) == secret

        secret = project.modules_config.config.get("gogs", {}).get("secret", "")
        secret = bytes(secret.encode("utf-8"))
        mac = hmac.new(secret, msg=request.body, digestmod=hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def _get_event_name(self, request):
        return "push"
