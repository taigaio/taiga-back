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

import json
import hmac
import hashlib

from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from taiga.base.api.viewsets import GenericViewSet
from taiga.projects.models import Project

from . import event_hooks
from .exceptions import ActionSyntaxException


class Http400(APIException):
    status_code = 400


class GitHubViewSet(GenericViewSet):
    # We don't want rest framework to parse the request body and transform it in
    # a dict in request.DATA, we need it raw
    parser_classes = ()

    # This dict associates the event names we are listening for
    # with their reponsible classes (extending event_hooks.BaseEventHook)
    event_hook_classes = {
        "push": event_hooks.PushEventHook,
        "issues": event_hooks.IssuesEventHook,
        "issue_comment": event_hooks.IssueCommentEventHook,
    }

    def _validate_signature(self, project, request):
        x_hub_signature = request.META.get("HTTP_X_HUB_SIGNATURE", None)
        if not x_hub_signature:
            return False

        sha_name, signature = x_hub_signature.split('=')
        if sha_name != 'sha1':
            return False

        if not hasattr(project, "modules_config"):
            return False

        if project.modules_config.config is None:
            return False

        secret = bytes(project.modules_config.config.get("github", {}).get("secret", "").encode("utf-8"))
        mac = hmac.new(secret, msg=request.body,digestmod=hashlib.sha1)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def _get_project(self, request):
        project_id = request.GET.get("project", None)
        try:
            project = Project.objects.get(id=project_id)
            return project
        except Project.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        project = self._get_project(request)
        if not project:
            raise Http400(_("The project doesn't exist"))

        if not self._validate_signature(project, request):
            raise Http400(_("Bad signature"))

        event_name = request.META.get("HTTP_X_GITHUB_EVENT", None)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except ValueError as e:
            raise Http400(_("The payload is not a valid json"))

        event_hook_class = self.event_hook_classes.get(event_name, None)
        if event_hook_class is not None:
            event_hook = event_hook_class(project, payload)
            try:
                event_hook.process_event()
            except ActionSyntaxException as e:
                raise Http400(e)

        return Response({})
