# -*- coding: utf-8 -*-
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

from django.conf import settings

from ipware.ip import get_ip

from taiga.base.utils import json

from taiga.projects.models import Project
from taiga.hooks.api import BaseWebhookApiViewSet

from . import event_hooks

from netaddr import all_matching_cidrs
from netaddr.core import AddrFormatError

class GitLabViewSet(BaseWebhookApiViewSet):
    event_hook_classes = {
        "push": event_hooks.PushEventHook,
        "issue": event_hooks.IssuesEventHook,
        "note": event_hooks.IssueCommentEventHook,
    }

    def _validate_signature(self, project, request):
        secret_key = request.GET.get("key", None)

        if secret_key is None:
            return False

        if not hasattr(project, "modules_config"):
            return False

        if project.modules_config.config is None:
            return False

        project_secret = project.modules_config.config.get("gitlab", {}).get("secret", "")
        if not project_secret:
            return False

        gitlab_config = project.modules_config.config.get("gitlab", {})
        valid_origin_ips = gitlab_config.get("valid_origin_ips", settings.GITLAB_VALID_ORIGIN_IPS)
        origin_ip = get_ip(request)
        mathching_origin_ip = True

        if valid_origin_ips:
            try:
                mathching_origin_ip = len(all_matching_cidrs(origin_ip,valid_origin_ips)) > 0

            except (AddrFormatError, ValueError):
                mathching_origin_ip = False

        if not mathching_origin_ip:
            return False

        return project_secret == secret_key

    def _get_event_name(self, request):
        payload = json.loads(request.body.decode("utf-8"))
        return payload.get('object_kind', 'push') if payload is not None else 'empty'
