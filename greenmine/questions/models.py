from django.db import models

from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.fields import DictField


class Question(models.Model):
    subject = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=250, blank=True)
    content = models.TextField(blank=True)
    closed = models.BooleanField(default=False)
    attached_file = models.FileField(upload_to="messages", max_length=500,
                                     null=True, blank=True)

    project = models.ForeignKey('scrum.Project', related_name='questions')
    milestone = models.ForeignKey('scrum.Milestone', related_name='questions',
                                  null=True, default=None, blank=True)

    assigned_to = models.ForeignKey("base.User")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('base.User', related_name='questions')

    watchers = models.ManyToManyField('base.User',
                                      related_name='question_watch', null=True,
                                      blank=True)
    tags = DictField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.subject, self.__class__)
        super(Question, self).save(*args, **kwargs)


class QuestionResponse(models.Model):
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="messages", max_length=500,
                                     null=True, blank=True)

    question = models.ForeignKey('Question', related_name='responses')
    owner = models.ForeignKey('base.User', related_name='questions_responses')
    tags = DictField()
