# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
