#
from django.apps import AppConfig


class WikiAppConfig(AppConfig):
    name = "taiga.projects.wiki"
    verbose_name = "Wiki"
    watched_types = ["wiki.wiki_page", ]
