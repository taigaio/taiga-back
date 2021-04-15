# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import JSONField as DjangoJSONField


__all__ = ["JSONField"]


class JSONField(DjangoJSONField):
    def __init__(self, verbose_name=None, name=None, encoder=DjangoJSONEncoder, **kwargs):
        super().__init__(verbose_name, name, encoder, **kwargs)
