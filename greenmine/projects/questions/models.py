# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver

from greenmine.base.utils.slug import ref_uniquely

from picklefield.fields import PickledObjectField

from . import choices


class QuestionStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is closed'))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                related_name='question_status',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'question status'
        verbose_name_plural = u'question status'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class Question(models.Model):

    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                verbose_name=_('ref'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                related_name='owned_questions',
                verbose_name=_('owner'))
    status = models.ForeignKey('QuestionStatus', null=False, blank=False,
                related_name='questions',
                verbose_name=_('status'))
    subject = models.CharField(max_length=250, null=False, blank=False,
                verbose_name=_('subject'))
    content = models.TextField(null=False, blank=True,
                verbose_name=_('content'))
    closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('closed'))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                upload_to='messages',
                verbose_name=_('attached_file'))
    project = models.ForeignKey('projects.Project', null=False, blank=False,
                related_name='questions',
                verbose_name=_('project'))
    milestone = models.ForeignKey('milestones.Milestone', null=True, blank=True, default=None,
                related_name='questions',
                verbose_name=_('milestone'))
    finished_date = models.DateTimeField(null=True, blank=True,
                verbose_name=_('finished date'))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                related_name='questions_assigned_to_me',
                verbose_name=_('assigned_to'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('modified date'))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                related_name='watched_questions',
                verbose_name=_('watchers'))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'question'
        verbose_name_plural = u'questions'
        ordering = ['project', 'subject', 'id']
        #TODO: permissions
        permissions = (
            ('reply_question', 'Can reply questions'),
            ('change_owned_question', 'Can modify owned questions'),
            ('change_assigned_question', 'Can modify assigned questions'),
            ('assign_question_to_other', 'Can assign questions to others'),
            ('assign_question_to_myself', 'Can assign questions to myself'),
            ('change_question_state', 'Can change the question state'),
            ('view_question', 'Can view the question'),
        )

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, 'last_issue_ref', self.__class__)

        super(Question, self).save(*args, **kwargs)
