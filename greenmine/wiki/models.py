# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class WikiPage(models.Model):
    project = models.ForeignKey('scrum.Project', null=False, blank=False,
                related_name='wiki_pages',
                verbose_name=_('project'))
    slug = models.SlugField(max_length=500, db_index=True, null=False, blank=False,
                verbose_name=_('slug'))
    content = models.TextField(null=False, blank=True,
                verbose_name=_('content'))
    owner = models.ForeignKey('base.User', null=True, blank=True,
                related_name='owned_wiki_pages',
                verbose_name=_('owner'))
    watchers = models.ManyToManyField('base.User', null=True, blank=True,
                related_name='watched_wiki_pages',
                verbose_name=_('watchers'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))

    class Meta:
        verbose_name = u'wiki page'
        verbose_name_plural = u'wiki pages'
        ordering = ['project', 'slug']
        unique_together = ('project', 'slug',)

        permissions = (
            ('view_wikipage', 'Can modify owned wiki pages'),
            ('change_owned_wikipage', 'Can modify owned wiki pages'),
        )

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.subject)


class WikiPageAttachment(models.Model):
    wikipage = models.ForeignKey('WikiPage', null=False, blank=False,
                related_name='attachments',
                verbose_name=_('wiki page'))
    owner = models.ForeignKey('base.User', null=False, blank=False,
                related_name='owned_wiki_attachments',
                verbose_name=_('owner'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                upload_to='files/wiki',
                verbose_name=_('attached file'))

    class Meta:
        verbose_name = u'wiki page attachment'
        verbose_name_plural = u'wiki page attachments'
        ordering = ['wikipage', 'created_date']

    def __unicode__(self):
        return u'project {0} - page {1} - attachment {2}'.format(self.wikipage.project_id,
                                                                 self.wikipage.subject, self.id)
