# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import reversion


class WikiPage(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="wiki_pages", verbose_name=_("project"))
    slug = models.SlugField(max_length=500, db_index=True, null=False, blank=False,
                            verbose_name=_("slug"))
    content = models.TextField(null=False, blank=True,
                               verbose_name=_("content"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_wiki_pages", verbose_name=_("owner"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="watched_wiki_pages",
                                      verbose_name=_("watchers"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    attachments = generic.GenericRelation("projects.Attachment")

    class Meta:
        verbose_name = "wiki page"
        verbose_name_plural = "wiki pages"
        ordering = ["project", "slug"]
        unique_together = ("project", "slug",)
        permissions = (
            ("view_wikipage", "Can view wiki page"),
        )

    def __str__(self):
        return "project {0} - {1}".format(self.project_id, self.slug)


reversion.register(WikiPage)
