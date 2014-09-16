from django.db import models
from taiga.base import tags

class TaggedModel(tags.TaggedMixin, models.Model):
    class Meta:
        app_label = "tests"

