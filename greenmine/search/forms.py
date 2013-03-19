# -* coding: utf-8 -*-
from haystack import forms


class SearchForm(forms.SearchForm):
    def __init__(self, *args, **kwargs):
        kwargs['load_all'] = True
        super(SearchForm, self).__init__(*args, **kwargs)
