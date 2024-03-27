# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import importlib

from .. import models
from django.conf import settings


def get_modules_config(project):
    modules_config, created = models.ProjectModulesConfig.objects.get_or_create(project=project)

    if created or modules_config.config == None:
        modules_config.config = {}

    for key, configurator_function_name in settings.PROJECT_MODULES_CONFIGURATORS.items():
        mod_name, func_name = configurator_function_name.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        configurator = getattr(mod, func_name)
        modules_config.config[key] = configurator(project)

    modules_config.save()
    return modules_config
