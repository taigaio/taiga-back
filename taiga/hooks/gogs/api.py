# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

        signature = request.META.get("HTTP_X_GOGS_SIGNATURE", None)
        if not signature:  # Old format signature support (before 0.11 version)
            payload = self._get_payload(request)
            return payload.get('secret', None) == secret

        secret = project.modules_config.config.get("gogs", {}).get("secret", "")
        secret = bytes(secret.encode("utf-8"))
        mac = hmac.new(secret, msg=request.body, digestmod=hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def _get_event_name(self, request):
        return "push"
