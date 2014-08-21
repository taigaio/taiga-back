from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from taiga.projects.models import Project
from taiga.export_import.renderers import ExportRenderer
from taiga.export_import.service import project_to_dict

class Command(BaseCommand):
    args = '<project_slug project_slug ...>'
    help = 'Export a project to json'
    renderer_context = {"indent": 4}
    renderer = ExportRenderer()

    def handle(self, *args, **options):
        for project_slug in args:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise CommandError('Project "%s" does not exist' % project_slug)

            data = project_to_dict(project)
            print(self.renderer.render(data, renderer_context=self.renderer_context).decode('utf-8'))
