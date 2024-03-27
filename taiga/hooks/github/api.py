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


class GitHubViewSet(BaseWebhookApiViewSet):
    event_hook_classes = {
        "push": event_hooks.PushEventHook,
        "issues": event_hooks.IssuesEventHook,
        "issue_comment": event_hooks.IssueCommentEventHook,
    }

    def _validate_signature(self, project, request):
        x_hub_signature = request.headers.get("x-hub-signature", None)
        if not x_hub_signature:
            return False

        sha_name, signature = x_hub_signature.split('=')
        if sha_name != 'sha1':
            return False

        if not hasattr(project, "modules_config"):
            return False

        if project.modules_config.config is None:
            return False

        secret = project.modules_config.config.get("github", {}).get("secret", "")
        secret = bytes(secret.encode("utf-8"))
        mac = hmac.new(secret, msg=request.body, digestmod=hashlib.sha1)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def _get_event_name(self, request):
        return request.headers.get("x-github-event", None)
