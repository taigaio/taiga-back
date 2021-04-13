# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.fields import Field


class StorageEntrySerializer(serializers.LightSerializer):
    key = Field()
    value = Field()
    created_date = Field()
    modified_date = Field()
