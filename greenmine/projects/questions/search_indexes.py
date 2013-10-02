# -* coding: utf-8 -*-

from haystack import indexes

from . import models


class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                             template_name='search/indexes/question_text.txt')
    title = indexes.CharField(model_attr='subject')

    def get_model(self):
        return models.Question

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
