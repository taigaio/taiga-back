# -* coding: utf-8 -*-

from haystack import indexes
from greenmine.scrum.models import UserStory, Task, Issue


class UserStoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                             template_name='search/indexes/userstory_text.txt')
    title = indexes.CharField(model_attr='subject')
    project_id = indexes.IntegerField(model_attr="project_id")
    description = indexes.CharField(model_attr="description")

    def get_model(self):
        return UserStory

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class TaskIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                             template_name='search/indexes/task_text.txt')
    title = indexes.CharField(model_attr='subject')
    project_id = indexes.IntegerField(model_attr="project_id")
    description = indexes.CharField(model_attr="description")

    def get_model(self):
        return Task

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class IssueIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                             template_name='search/indexes/issue_text.txt')
    title = indexes.CharField(model_attr='subject')
    project_id = indexes.IntegerField(model_attr="project_id")
    description = indexes.CharField(model_attr="description")

    def get_model(self):
        return Issue

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
