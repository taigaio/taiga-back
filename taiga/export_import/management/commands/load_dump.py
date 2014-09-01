from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import signals
from optparse import make_option

import json
import pprint

from taiga.projects.models import Project
from taiga.export_import.renderers import ExportRenderer
from taiga.export_import.dump_service import dict_to_project, TaigaImportError
from taiga.export_import.service import get_errors

class Command(BaseCommand):
    args = '<dump_file> <owner-email>'
    help = 'Export a project to json'
    renderer_context = {"indent": 4}
    renderer = ExportRenderer()
    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Delete project if exists'),
        )

    def handle(self, *args, **options):
        data = json.loads(open(args[0], 'r').read())
        try:
            with transaction.atomic():
                if options["overwrite"]:
                    receivers_back = signals.post_delete.receivers
                    signals.post_delete.receivers = []
                    try:
                        proj = Project.objects.get(slug=data.get("slug", "not a slug"))
                        proj.tasks.all().delete()
                        proj.user_stories.all().delete()
                        proj.issues.all().delete()
                        proj.memberships.all().delete()
                        proj.roles.all().delete()
                        proj.delete()
                    except Project.DoesNotExist:
                        pass
                    signals.post_delete.receivers = receivers_back
                dict_to_project(data, args[1])
        except TaigaImportError as e:
            print("ERROR:", end=" ")
            print(e.message)
            print(get_errors())
