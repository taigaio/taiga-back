# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import JSONField as DjangoJSONField


__all__ = ["JSONField"]


class JSONField(DjangoJSONField):
    def __init__(self, verbose_name=None, name=None, encoder=DjangoJSONEncoder, **kwargs):
        super().__init__(verbose_name, name, encoder, **kwargs)
