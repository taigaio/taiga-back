# -* coding: utf-8 -*-
from haystack import indexes
from .models import Question


class QuestionIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/indexes/question_text.txt')

    def get_model(self):
        return Question

    def index_queryset(self):
        return self.get_model().objects.all()
