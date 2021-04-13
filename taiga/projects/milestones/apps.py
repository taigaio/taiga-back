#
from django.apps import AppConfig


class MilestonesAppConfig(AppConfig):
    name = "taiga.projects.milestones"
    verbose_name = "Milestones"
    watched_types = ["milestones.milestone", ]
