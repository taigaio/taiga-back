from django.db import models
from django.utils.translation import ugettext_lazy as _

from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.fields import DictField


class Question(models.Model):
    subject = models.CharField(max_length=150, null=False, blank=False,
                verbose_name=_('subject'))
    slug = models.SlugField(unique=True, max_length=250, null=False, blank=True,
                verbose_name=_('slug'))
    content = models.TextField(null=False, blank=True,
                verbose_name=_('content'))
    closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('closed'))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                upload_to='messages',
                verbose_name=_('attached_file'))
    project = models.ForeignKey('scrum.Project', null=False, blank=False,
                related_name='questions')
    milestone = models.ForeignKey('scrum.Milestone', null=True, blank=True, default=None,
                related_name='questions',
                verbose_name=_('milestone'))
    assigned_to = models.ForeignKey('base.User', null=False, blank=False,
                related_name='questions_assigned_to_me',
                verbose_name=_('assigned_to'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('modified date'))
    owner = models.ForeignKey('base.User', null=False, blank=False,
                related_name='owned_questions')
    watchers = models.ManyToManyField('base.User', null=True, blank=True,
                related_name='watched_questions',
                verbose_name=_('watchers'))
    tags = DictField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'question'
        verbose_name_plural = u'questions'
        ordering = ['project', 'subject', 'id']
        permissions = (
            ('can_reply_question', 'Can reply questions'),
            ('can_change_owned_question', 'Can modify owned questions'),
        )

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.subject, self.__class__)
        super(Question, self).save(*args, **kwargs)


class QuestionResponse(models.Model):
    content = models.TextField(null=False, blank=False,
                verbose_name=_('content'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                upload_to='messages',
                verbose_name=_('attached file'))
    question = models.ForeignKey('Question', null=False, blank=False,
                related_name='responses',
                verbose_name=_('question'))
    owner = models.ForeignKey('base.User', null=False, blank=False,
                related_name='question_responses')
    tags = DictField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'question response'
        verbose_name_plural = u'question responses'
        ordering = ['question', 'created_date']

    def __unicode__(self):
        return u'{0} - response {1}'.format(unicode(self.question), self.id)

