# -* coding: utf-8 -*-
from haystack import indexes
from .models import Document


class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/indexes/document_text.txt')
    title = indexes.CharField(model_attr='title')

    def get_model(self):
        return Document

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
