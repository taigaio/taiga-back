# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField


class FanSerializer(serializers.LightSerializer):
    id = Field()
    username = Field()
    full_name = MethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()
