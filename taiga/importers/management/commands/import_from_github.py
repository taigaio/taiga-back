# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from taiga.importers.github.importer import GithubImporter
from taiga.users.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--token', dest="token", type=str,
                            help='Auth token')
        parser.add_argument('--project-id', dest="project_id", type=str,
                            help='Project ID or full name (ex: taigaio/taiga-back)')
        parser.add_argument('--template', dest='template', default="kanban",
                            help='template to use: scrum or kanban (default kanban)')
        parser.add_argument('--type', dest='type', default="user_stories",
                            help='type of object to use: user_stories or issues (default user_stories)')
        parser.add_argument('--ask-for-users', dest='ask_for_users', const=True,
                            action="store_const", default=False,
                            help='Import closed data')
        parser.add_argument('--keep-external-reference', dest='keep_external_reference', const=True,
                            action="store_const", default=False,
                            help='Store external reference of imported data')

    def handle(self, *args, **options):
        admin = User.objects.get(username="admin")

        if options.get('token', None):
            token = options.get('token')
        else:
            url = GithubImporter.get_auth_url(
                settings.IMPORTERS.get('github', {}).get('client_id', None)
            )
            print("Go to here and come with your code (in the redirected url): {}".format(url))
            code = input("Code: ")
            access_data = GithubImporter.get_access_token(
                settings.IMPORTERS.get('github', {}).get('client_id', None),
                settings.IMPORTERS.get('github', {}).get('client_secret', None),
                code
            )
            token = access_data

        importer = GithubImporter(admin, token)

        if options.get('project_id', None):
            project_id = options.get('project_id')
        else:
            print("Select the project to import:")
            for project in importer.list_projects():
                print("- {}: {}".format(project['id'], project['name']))
            project_id = input("Project id: ")

        users_bindings = {}
        if options.get('ask_for_users', None):
            print("Add the username or email for next github users:")

        for user in importer.list_users(project_id):
            while True:
                if user['detected_user'] is not None:
                    print("User automatically detected: {} as {}".format(user['full_name'], user['detected_user']))
                    users_bindings[user['id']] = user['detected_user']
                    break

                if not options.get('ask_for_users', False):
                    break

                username_or_email = input("{}: ".format(user['full_name'] or user['username']))
                if username_or_email == "":
                    break
                try:
                    users_bindings[user['id']] = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
                    break
                except User.DoesNotExist:
                    print("ERROR: Invalid username or email")

        options = {
            "template": options.get('template'),
            "type": options.get('type'),
            "users_bindings": users_bindings,
            "keep_external_reference": options.get('keep_external_reference')
        }

        importer.import_project(project_id, options)
