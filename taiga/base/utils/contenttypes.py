# -*- coding: utf-8 -*-
from django.apps import apps
from django.contrib.contenttypes.management import create_contenttypes


def update_all_contenttypes(**kwargs):
    for app_config in apps.get_app_configs():
        create_contenttypes(app_config, **kwargs)
