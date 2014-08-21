from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

import json

from taiga.projects.models import Project
from taiga.export_import.renderers import ExportRenderer
from taiga.export_import.service import dict_to_project

class Command(BaseCommand):
    args = '<dump_file> <owner-email>'
    help = 'Export a project to json'
    renderer_context = {"indent": 4}
    renderer = ExportRenderer()

    def handle(self, *args, **options):
        data = json.loads(open(args[0], 'r').read())
        dict_to_project(data, args[1])
