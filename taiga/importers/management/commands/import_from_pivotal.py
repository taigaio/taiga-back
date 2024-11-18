# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand
from django.db.models import Q

from taiga.importers.pivotal.importer import PivotalImporter
from taiga.users.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--token', dest="token", type=str,
                            help='Auth token')
        parser.add_argument('--project-id', dest="project_id", type=str,
                            help='Project ID or full name (ex: taigaio/taiga-back)')
        parser.add_argument('--template', dest='template', default="scrum",
                            help='template to use: scrum or kanban (default scrum)')
        parser.add_argument('--map-users', dest='map_users', const=True,
                            action="store_const", default=False,
                            help='Map usernames from Pivotal to Taiga. You can create users in Taiga in advance via /admin/users/user')
        parser.add_argument('--closed-data', dest='closed_data', const=True,
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
            print("You need a user token")
            return

        importer = PivotalImporter(admin, token)

        if options.get('project_id', None):
            project_id = options.get('project_id')
        else:
            print("Select the project to import:")
            for project in importer.list_projects():
                print("- {}: {}".format(project['project_id'], project['project_name']))
            project_id = input("Project id: ")

        users_bindings = {}
        if options.get('map_users', None):
            for user in importer.list_users(project_id):
                try:
                    users_bindings[user['person']['id']] = User.objects.get(Q(email=user['person'].get('email', "not-valid")))
                except User.DoesNotExist:
                    pass

        options = {
            "template": options.get('template'),
            "import_closed_data": options.get("closed_data", False),
            "users_bindings": users_bindings,
            "keep_external_reference": options.get('keep_external_reference')
        }
        importer.import_project(project_id, options)
