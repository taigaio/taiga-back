from django.db import models
from greenmine.core.utils.slug import slugify_uniquely
from greenmine.taggit.managers import TaggableManager


class Question(models.Model):
    subject = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=250, blank=True)
    content = models.TextField(blank=True)
    closed = models.BooleanField(default=False)
    attached_file = models.FileField(upload_to="messages",
        max_length=500, null=True, blank=True)

    project = models.ForeignKey('scrum.Project', related_name='questions')
    milestone = models.ForeignKey('scrum.Milestone', related_name='questions',
        null=True, default=None, blank=True)

    assigned_to = models.ForeignKey("auth.User")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='questions')


    watchers = models.ManyToManyField('auth.User',
        related_name='question_watch', null=True, blank=True)

    tags = TaggableManager()

    @models.permalink
    def get_absolute_url(self):
        return self.get_view_url()

    @models.permalink
    def get_view_url(self):
        return ('questions-view', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    @models.permalink
    def get_edit_url(self):
        return ('questions-edit', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    @models.permalink
    def get_delete_url(self):
        return ('questions-delete', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.subject, self.__class__)
        super(Question, self).save(*args, **kwargs)


class QuestionResponse(models.Model):
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="messages",
        max_length=500, null=True, blank=True)

    question = models.ForeignKey('Question', related_name='responses')
    owner = models.ForeignKey('auth.User', related_name='questions_responses')


