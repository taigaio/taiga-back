# -* coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from greenmine.core.utils.slug import slugify_uniquely as slugify
from greenmine.taggit.managers import TaggableManager


class Document(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    description = models.TextField(blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey('scrum.Project', related_name='documents')
    owner = models.ForeignKey('auth.User', related_name='documents')
    attached_file = models.FileField(upload_to="documents",
        max_length=1000, null=True, blank=True)

    tags = TaggableManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, self.__class__)
        super(Document, self).save(*args, **kwargs)

    @models.permalink
    def get_delete_url(self):
        return ('documents-delete', (),
            {'pslug': self.project.slug, 'docid': self.pk})

    @models.permalink
    def get_absolute_url(self):
        return self.attached_file.url
