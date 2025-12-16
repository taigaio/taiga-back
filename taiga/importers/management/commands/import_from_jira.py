# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings

from taiga.importers.jira.agile import JiraAgileImporter
from taiga.importers.jira.normal import JiraNormalImporter
from taiga.users.models import User

import json
from abc import ABC, abstractmethod


class AuthTokenStrategy(ABC):
    @abstractmethod
    def resolve(self, server):
        raise NotImplementedError


class AnonTokenStrategy(AuthTokenStrategy):
    def resolve(self, server):
        return None


class ProvidedTokenStrategy(AuthTokenStrategy):
    def __init__(self, raw_token):
        self.raw_token = raw_token

    def resolve(self, server):
        return json.loads(self.raw_token)


class InteractiveTokenStrategy(AuthTokenStrategy):
    def resolve(self, server):
        (rtoken, rtoken_secret, url) = JiraNormalImporter.get_auth_url(
            server,
            settings.IMPORTERS.get('jira', {}).get('consumer_key', None),
            settings.IMPORTERS.get('jira', {}).get('cert', None),
            True
        )
        print(url)
        input("Go to the url, allow the user and get back and press enter")
        token = JiraNormalImporter.get_access_token(
            server,
            settings.IMPORTERS.get('jira', {}).get('consumer_key', None),
            settings.IMPORTERS.get('jira', {}).get('cert', None),
            rtoken,
            rtoken_secret,
            True
        )
        print("Auth token: {}".format(json.dumps(token)))
        return token


class ImportStrategy(ABC):
    def __init__(self, admin_user, server, auth_token):
        self.admin_user = admin_user
        self.server = server
        self.auth_token = auth_token

    @abstractmethod
    def build_importer(self):
        raise NotImplementedError

    @abstractmethod
    def import_data(self, importer, project_id, options):
        raise NotImplementedError


class ProjectImportStrategy(ImportStrategy):
    def build_importer(self):
        return JiraNormalImporter(self.admin_user, self.server, self.auth_token)

    def import_data(self, importer, project_id, options):
        print("Bind jira issue types to (epic, us, issue)")
        types_bindings = {
            "epic": [],
            "us": [],
            "task": [],
            "issue": [],
        }

        for issue_type in importer.list_issue_types(project_id):
            self._bind_issue_type(types_bindings, issue_type)
        options["types_bindings"] = types_bindings
        importer.import_project(project_id, options)

    def _bind_issue_type(self, types_bindings, issue_type):
        if issue_type['subtask']:
            types_bindings['task'].append(issue_type)
            return

        while True:
            taiga_type = input("{}: ".format(issue_type['name']))
            if taiga_type not in ['epic', 'us', 'issue']:
                print("use a valid taiga type (epic, us, issue)")
                continue

            types_bindings[taiga_type].append(issue_type)
            break


class BoardImportStrategy(ImportStrategy):
    def build_importer(self):
        return JiraAgileImporter(self.admin_user, self.server, self.auth_token)

    def import_data(self, importer, project_id, options):
        importer.import_board(project_id, options)


class UserBindingPrompter:
    def __init__(self, importer):
        self.importer = importer

    def prompt(self):
        bindings = {}
        print("Add the username or email for next jira users:")
        for user in self.importer.list_users():
            try:
                bindings[user['key']] = User.objects.get(Q(email=user['email']))
                break
            except User.DoesNotExist:
                pass

            while True:
                username_or_email = input("{}: ".format(user['full_name']))
                if username_or_email == "":
                    break
                try:
                    bindings[user['key']] = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
                    break
                except User.DoesNotExist:
                    print("ERROR: Invalid username or email")
        return bindings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--token', dest="token", type=str,
                            help='Auth token')
        parser.add_argument('--server', dest="server", type=str,
                            help='Server address (default: https://jira.atlassian.com)',
                            default="https://jira.atlassian.com")
        parser.add_argument('--project-id', dest="project_id", type=str,
                            help='Project ID or full name (ex: taigaio/taiga-back)')
        parser.add_argument('--project-type', dest="project_type", type=str,
                            help='Project type in jira: project or board')
        parser.add_argument('--template', dest='template', default="scrum",
                            help='template to use: scrum or kanban (default scrum)')
        parser.add_argument('--ask-for-users', dest='ask_for_users', const=True,
                            action="store_const", default=False,
                            help='Import closed data')
        parser.add_argument('--closed-data', dest='closed_data', const=True,
                            action="store_const", default=False,
                            help='Import closed data')
        parser.add_argument('--keep-external-reference', dest='keep_external_reference', const=True,
                            action="store_const", default=False,
                            help='Store external reference of imported data')

    def handle(self, *args, **options):
        admin_user = User.objects.get(username="admin")
        server = options.get("server")

        token_option = options.get('token', None)
        auth_token = self._resolve_auth_token(token_option, server)

        project_type_option = options.get('project_type', None)
        selected_project_type = self._choose_project_type(project_type_option)

        strategy_map = {
            "project": ProjectImportStrategy(admin_user, server, auth_token),
            "board": BoardImportStrategy(admin_user, server, auth_token),
        }
        strategy = strategy_map.get(selected_project_type)
        if strategy is None:
            print("ERROR: Bad project type.")
            return

        importer = strategy.build_importer()
        options_project_id = options.get('project_id', None)
        project_id = self._select_project_id(importer, options_project_id)

        users_bindings = {}
        if options.get('ask_for_users', None):
            users_bindings = UserBindingPrompter(importer).prompt()

        options = {
            "template": options.get('template'),
            "import_closed_data": options.get("closed_data", False),
            "users_bindings": users_bindings,
            "keep_external_reference": options.get('keep_external_reference'),
        }

        strategy.import_data(importer, project_id, options)

    def _resolve_auth_token(self, token_option, server):
        strategy = self._choose_auth_strategy(token_option)
        return strategy.resolve(server)

    def _choose_auth_strategy(self, token_option):
        if token_option == "anon":
            return AnonTokenStrategy()
        if token_option:
            return ProvidedTokenStrategy(token_option)
        return InteractiveTokenStrategy()

    def _choose_project_type(self, project_type_option):
        if project_type_option is None:
            print("Select the type of project to import (project or board): ")
            return input("Project type: ")
        return project_type_option

    def _select_project_id(self, importer, options_project_id):
        if options_project_id:
            return options_project_id
        print("Select the project to import:")
        for project in importer.list_projects():
            print("- {}: {}".format(project['id'], project['name']))
        return input("Project id or key: ")
