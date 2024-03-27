# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid

from django.utils.translation import gettext as _
from django.conf import settings

from taiga.base.api import viewsets
from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.users.models import AuthData, User
from taiga.users.services import get_user_photo_url
from taiga.users.gravatar import get_user_gravatar_id

from taiga.importers import permissions
from taiga.importers import exceptions
from taiga.importers.services import resolve_users_bindings
from .normal import JiraNormalImporter
from .agile import JiraAgileImporter
from . import tasks


class JiraImporterViewSet(viewsets.ViewSet):
    permission_classes = (permissions.ImporterPermission,)

    def _get_token(self, request):
        token_data = request.DATA.get('token', "").split(".")

        token = {
            "access_token": token_data[0],
            "access_token_secret": token_data[1],
            "key_cert": settings.IMPORTERS.get('jira', {}).get('cert', None),
            "consumer_key": settings.IMPORTERS.get('jira', {}).get('consumer_key', None)
        }
        return token

    @list_route(methods=["POST"])
    def list_users(self, request, *args, **kwargs):
        self.check_permissions(request, "list_users", None)

        url = request.DATA.get('url', None)
        token = self._get_token(request)
        project_id = request.DATA.get('project', None)

        if not project_id:
            raise exc.WrongArguments(_("The project param is needed"))
        if not url:
            raise exc.WrongArguments(_("The url param is needed"))

        importer = JiraNormalImporter(request.user, url, token)
        try:
            users = importer.list_users()
        except Exception as e:
            # common error due to modern Jira versions which are unsupported by Taiga
            raise exc.BadRequest(_("""
                There was an error; probably due to an unsupported Jira version.
                Taiga does not support Jira releases from 8.6."""
            ))

        for user in users:
            user['user'] = None
            if not user['email']:
                continue

            try:
                taiga_user = User.objects.get(email=user['email'])
            except User.DoesNotExist:
                continue

            user['user'] = {
                'id': taiga_user.id,
                'full_name': taiga_user.get_full_name(),
                'gravatar_id': get_user_gravatar_id(taiga_user),
                'photo': get_user_photo_url(taiga_user),
            }
        return response.Ok(users)

    @list_route(methods=["POST"])
    def list_projects(self, request, *args, **kwargs):
        self.check_permissions(request, "list_projects", None)
        url = request.DATA.get('url', None)
        if not url:
            raise exc.WrongArguments(_("The url param is needed"))

        token = self._get_token(request)
        importer = JiraNormalImporter(request.user, url, token)
        agile_importer = JiraAgileImporter(request.user, url, token)
        projects = importer.list_projects()
        boards = agile_importer.list_projects()
        return response.Ok(sorted(projects + boards, key=lambda x: x['name']))

    @list_route(methods=["POST"])
    def import_project(self, request, *args, **kwargs):
        self.check_permissions(request, "import_project", None)

        url = request.DATA.get('url', None)
        token = self._get_token(request)
        project_id = request.DATA.get('project', None)
        if not project_id:
            raise exc.WrongArguments(_("The project param is needed"))

        if not url:
            raise exc.WrongArguments(_("The url param is needed"))

        options = {
            "name": request.DATA.get('name', None),
            "description": request.DATA.get('description', None),
            "users_bindings": resolve_users_bindings(request.DATA.get("users_bindings", {})),
            "keep_external_reference": request.DATA.get("keep_external_reference", False),
            "is_private": request.DATA.get("is_private", False),
        }

        importer_type = request.DATA.get('importer_type', "normal")
        if importer_type == "agile":
            importer = JiraAgileImporter(request.user, url, token)
        else:
            project_type = request.DATA.get("project_type", "scrum")
            if project_type == "kanban":
                options['template'] = "kanban"
            else:
                options['template'] = "scrum"

            importer = JiraNormalImporter(request.user, url, token)

            types_bindings = {
                "epic": [],
                "us": [],
                "task": [],
                "issue": [],
            }
            for issue_type in importer.list_issue_types(project_id):
                if project_type in ['scrum', 'kanban']:
                    # Set the type bindings
                    if issue_type['subtask']:
                        types_bindings['task'].append(issue_type)
                    elif issue_type['name'].upper() == "EPIC":
                        types_bindings["epic"].append(issue_type)
                    elif issue_type['name'].upper() in ["US", "USERSTORY", "USER STORY"]:
                        types_bindings["us"].append(issue_type)
                    elif issue_type['name'].upper() in ["ISSUE", "BUG", "ENHANCEMENT"]:
                        types_bindings["issue"].append(issue_type)
                    else:
                        types_bindings["us"].append(issue_type)
                elif project_type == "issues":
                    # Set the type bindings
                    if issue_type['subtask']:
                        continue
                    types_bindings["issue"].append(issue_type)
                elif project_type == "issues-with-subissues":
                    types_bindings["issue"].append(issue_type)
                else:
                    raise exc.WrongArguments(_("Invalid project_type {}").format(project_type))

            options["types_bindings"] = types_bindings

        if settings.CELERY_ENABLED:
            task = tasks.import_project.delay(request.user.id, url, token, project_id, options, importer_type)
            return response.Accepted({"task_id": task.id})

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
        jira_url = request.QUERY_PARAMS.get('url', None)

        if not jira_url:
            raise exc.WrongArguments(_("The url param is needed"))

        try:
            (oauth_token, oauth_secret, url) = JiraNormalImporter.get_auth_url(
                jira_url,
                settings.IMPORTERS.get('jira', {}).get('consumer_key', None),
                settings.IMPORTERS.get('jira', {}).get('cert', None),
                True
            )
        except exceptions.InvalidServiceConfiguration:
            raise exc.BadRequest(_("Invalid Jira server configuration."))

        (auth_data, created) = AuthData.objects.get_or_create(
            user=request.user,
            key="jira-oauth",
            defaults={
                "value": uuid.uuid4().hex,
                "extra": {},
            }
        )
        auth_data.extra = {
            "oauth_token": oauth_token,
            "oauth_secret": oauth_secret,
            "url": jira_url,
        }
        auth_data.save()

        return response.Ok({"url": url})

    @list_route(methods=["POST"])
    def authorize(self, request, *args, **kwargs):
        self.check_permissions(request, "authorize", None)

        try:
            oauth_data = request.user.auth_data.get(key="jira-oauth")
            oauth_verifier = request.DATA.get("oauth_verifier", None)
            oauth_token = oauth_data.extra['oauth_token']
            oauth_secret = oauth_data.extra['oauth_secret']
            server_url = oauth_data.extra['url']
            oauth_data.delete()

            jira_token = JiraNormalImporter.get_access_token(
                server_url,
                settings.IMPORTERS.get('jira', {}).get('consumer_key', None),
                settings.IMPORTERS.get('jira', {}).get('cert', None),
                oauth_token,
                oauth_secret,
                oauth_verifier,
                False
            )
        except Exception as e:
            raise exc.WrongArguments(_("Invalid or expired auth token"))

        return response.Ok({
            "token": jira_token['access_token'] + "." + jira_token['access_token_secret'],
            "url": server_url
        })
