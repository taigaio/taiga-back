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
                            help='template to use: scrum or scrum (default scrum)')
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
        admin = User.objects.get(username="admin")
        server = options.get("server")

        if options.get('token', None) == "anon":
            token = None
        elif options.get('token', None):
            token = json.loads(options.get('token'))
        else:
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


        if options.get('project_type', None) is None:
            print("Select the type of project to import (project or board): ")
            project_type = input("Project type: ")
        else:
            project_type = options.get('project_type')

        if project_type not in ["project", "board"]:
            print("ERROR: Bad project type.")
            return

        if project_type == "project":
            importer = JiraNormalImporter(admin, server, token)
        else:
            importer = JiraAgileImporter(admin, server, token)

        if options.get('project_id', None):
            project_id = options.get('project_id')
        else:
            print("Select the project to import:")
            for project in importer.list_projects():
                print("- {}: {}".format(project['id'], project['name']))
            project_id = input("Project id or key: ")

        users_bindings = {}
        if options.get('ask_for_users', None):
            print("Add the username or email for next jira users:")
            for user in importer.list_users():
                try:
                    users_bindings[user['key']] = User.objects.get(Q(email=user['email']))
                    break
                except User.DoesNotExist:
                    pass

                while True:
                    username_or_email = input("{}: ".format(user['full_name']))
                    if username_or_email == "":
                        break
                    try:
                        users_bindings[user['key']] = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
                        break
                    except User.DoesNotExist:
                        print("ERROR: Invalid username or email")

        options = {
            "template": options.get('template'),
            "import_closed_data": options.get("closed_data", False),
            "users_bindings": users_bindings,
            "keep_external_reference": options.get('keep_external_reference'),
        }

        if project_type == "project":
            print("Bind jira issue types to (epic, us, issue)")
            types_bindings = {
                "epic": [],
                "us": [],
                "task": [],
                "issue": [],
            }

            for issue_type in importer.list_issue_types(project_id):
                while True:
                    if issue_type['subtask']:
                        types_bindings['task'].append(issue_type)
                        break

                    taiga_type = input("{}: ".format(issue_type['name']))
                    if taiga_type not in ['epic', 'us', 'issue']:
                        print("use a valid taiga type (epic, us, issue)")
                        continue

                    types_bindings[taiga_type].append(issue_type)
                    break
            options["types_bindings"] = types_bindings

        importer.import_project(project_id, options)
