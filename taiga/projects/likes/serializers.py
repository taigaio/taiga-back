# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField


class FanSerializer(serializers.LightSerializer):
    id = Field()
    username = Field()
    full_name = MethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()
