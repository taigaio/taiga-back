# -*- coding: utf-8 -*-
from taiga.base.api import validators
from taiga.base.api import serializers
from taiga.projects.notifications.validators import WatchersValidator

from . import models


class WikiPageValidator(WatchersValidator, validators.ModelValidator):
    slug = serializers.CharField()

    class Meta:
        model = models.WikiPage
        read_only_fields = ('modified_date', 'created_date', 'owner')


class WikiLinkValidator(validators.ModelValidator):
    class Meta:
        model = models.WikiLink
        read_only_fields = ('href',)
