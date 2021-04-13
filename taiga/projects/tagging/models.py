# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import ugettext_lazy as _


class TaggedMixin(models.Model):
    tags = ArrayField(models.TextField(),
                      null=True, blank=True, default=list, verbose_name=_("tags"))

    class Meta:
        abstract = True


class TagsColorsMixin(models.Model):
    tags_colors = ArrayField(ArrayField(models.TextField(null=True, blank=True), size=2),
                             null=True, blank=True, default=list, verbose_name=_("tags colors"))

    class Meta:
        abstract = True
