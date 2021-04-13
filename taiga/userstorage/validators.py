# -*- coding: utf-8 -*-
from taiga.base.api import validators

from . import models


class StorageEntryValidator(validators.ModelValidator):
    class Meta:
        model = models.StorageEntry
        fields = ("key", "value")
