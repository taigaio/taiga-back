# -* coding: utf-8 -*-

from haystack import indexes
from . import models


class UserStoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                             template_name='search/indexes/userstory_text.txt')
    title = indexes.CharField(model_attr='subject')
    project_id = indexes.IntegerField(model_attr="project_id")
    description = indexes.CharField(model_attr="description")

    def get_model(self):
        return models.UserStory

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
