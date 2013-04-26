# -* coding: utf-8 -*-

from haystack import indexes
from .models import WikiPage


class WikiPageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/indexes/wikipage_text.txt')

    def get_model(self):
        return WikiPage

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
