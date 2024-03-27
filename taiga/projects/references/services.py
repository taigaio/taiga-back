# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps


def get_instance_by_ref(project_id, obj_ref):
    model_cls = apps.get_model("references", "Reference")
    try:
        instance = model_cls.objects.get(project_id=project_id, ref=obj_ref)
    except model_cls.DoesNotExist:
        instance = None

    return instance
