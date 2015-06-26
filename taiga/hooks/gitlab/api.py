# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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


class GitLabViewSet(BaseWebhookApiViewSet):
    event_hook_classes = {
        "push": event_hooks.PushEventHook,
        "issue": event_hooks.IssuesEventHook,
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
        if valid_origin_ips and (not origin_ip or origin_ip not in valid_origin_ips):
            return False

        return project_secret == secret_key

    def _get_project(self, request):
        project_id = request.GET.get("project", None)
        try:
            project = Project.objects.get(id=project_id)
            return project
        except Project.DoesNotExist:
            return None

    def _get_event_name(self, request):
        payload = json.loads(request.body.decode("utf-8"))
        return payload.get('object_kind', 'push')
