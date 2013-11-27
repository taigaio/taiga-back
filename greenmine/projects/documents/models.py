# -* coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField
from greenmine.base.utils.slug import slugify_uniquely as slugify


class Document(models.Model):
    slug = models.SlugField(unique=True, max_length=200, null=False, blank=True,
                verbose_name=_("slug"))
    title = models.CharField(max_length=150, null=False, blank=False,
                verbose_name=_("title"))
    description = models.TextField(null=False, blank=True,
                verbose_name=_("description"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_("modified date"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                related_name="documents",
                verbose_name=_("project"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                related_name="owned_documents",
                verbose_name=_("owner"))
    attached_file = models.FileField(max_length=1000, null=True, blank=True,
                upload_to="documents",
                verbose_name=_("attached_file"))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_("tags"))

    class Meta:
        verbose_name = u"Document"
        verbose_name_plural = u"Documents"
        ordering = ["project", "title",]
        permissions = (
            ("view_document", "Can view document"),
        )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, self.__class__)
        super().save(*args, **kwargs)

