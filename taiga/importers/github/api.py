# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _
from django.conf import settings

from taiga.base.api import viewsets
from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.users.services import get_user_photo_url
from taiga.users.gravatar import get_user_gravatar_id

from taiga.importers import permissions
from taiga.importers import exceptions
from taiga.importers.services import resolve_users_bindings
from .importer import GithubImporter
from . import tasks


class GithubImporterViewSet(viewsets.ViewSet):
    permission_classes = (permissions.ImporterPermission,)

    @list_route(methods=["POST"])
    def list_users(self, request, *args, **kwargs):
        self.check_permissions(request, "list_users", None)

        token = request.DATA.get('token', None)
        project_id = request.DATA.get('project', None)

        if not project_id:
            raise exc.WrongArguments(_("The project param is needed"))

        importer = GithubImporter(request.user, token)
        users = importer.list_users(project_id)
        for user in users:
            if user['detected_user']:
                user['user'] = {
                    'id': user['detected_user'].id,
                    'full_name': user['detected_user'].get_full_name(),
                    'gravatar_id': get_user_gravatar_id(user['detected_user']),
                    'photo': get_user_photo_url(user['detected_user']),
                }
            del(user['detected_user'])
        return response.Ok(users)

    @list_route(methods=["POST"])
    def list_projects(self, request, *args, **kwargs):
        self.check_permissions(request, "list_projects", None)
        token = request.DATA.get('token', None)
        importer = GithubImporter(request.user, token)
        projects = importer.list_projects()
        return response.Ok(projects)

    @list_route(methods=["POST"])
    def import_project(self, request, *args, **kwargs):
        self.check_permissions(request, "import_project", None)

        token = request.DATA.get('token', None)
        project_id = request.DATA.get('project', None)
        if not project_id:
            raise exc.WrongArguments(_("The project param is needed"))

        template = request.DATA.get('template', "scrum")
        items_type = "user_stories"
        if template == "issues":
            items_type = "issues"
            template = "scrum"

        options = {
            "name": request.DATA.get('name', None),
            "description": request.DATA.get('description', None),
            "template": template,
            "type": items_type,
            "users_bindings": resolve_users_bindings(request.DATA.get("users_bindings", {})),
            "keep_external_reference": request.DATA.get("keep_external_reference", False),
            "is_private": request.DATA.get("is_private", False),
        }

        if settings.CELERY_ENABLED:
            task = tasks.import_project.delay(request.user.id, token, project_id, options)
            return response.Accepted({"task_id": task.id})

        importer = GithubImporter(request.user, token)
        project = importer.import_project(project_id, options)
        project_data = {
            "slug": project.slug,
            "my_permissions": ["view_us"],
            "is_backlog_activated": project.is_backlog_activated,
            "is_kanban_activated": project.is_kanban_activated,
        }

        return response.Ok(project_data)

    @list_route(methods=["GET"])
    def auth_url(self, request, *args, **kwargs):
        self.check_permissions(request, "auth_url", None)
        callback_uri = request.QUERY_PARAMS.get('uri')
        url = GithubImporter.get_auth_url(
            settings.IMPORTERS.get('github', {}).get('client_id', None),
            callback_uri
        )
        return response.Ok({"url": url})

    @list_route(methods=["POST"])
    def authorize(self, request, *args, **kwargs):
        self.check_permissions(request, "authorize", None)

        code = request.DATA.get('code', None)
        if code is None:
            raise exc.BadRequest(_("Code param needed"))

        try:
            token = GithubImporter.get_access_token(
                settings.IMPORTERS.get('github', {}).get('client_id', None),
                settings.IMPORTERS.get('github', {}).get('client_secret', None),
                code
            )
            return response.Ok({
                "token": token
            })
        except exceptions.InvalidAuthResult:
            raise exc.BadRequest(_("Invalid auth data"))
        except exceptions.FailedRequest:
            raise exc.BadRequest(_("Third party service failing"))
