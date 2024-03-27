# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.contrib.contenttypes.management import create_contenttypes


def update_all_contenttypes(**kwargs):
    for app_config in apps.get_app_configs():
        create_contenttypes(app_config, **kwargs)
