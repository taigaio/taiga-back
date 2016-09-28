# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django_pglocks import advisory_lock

from taiga.base.utils.slug import slugify_uniquely_for_queryset
from taiga.base.utils.time import timestamp_ms
from taiga.projects.notifications.mixins import WatchedModelMixin
from taiga.projects.occ import OCCModelMixin


class WikiPage(OCCModelMixin, WatchedModelMixin, models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="wiki_pages", verbose_name=_("project"))
    slug = models.SlugField(max_length=500, db_index=True, null=False, blank=False,
                            verbose_name=_("slug"))
    content = models.TextField(null=False, blank=True,
                               verbose_name=_("content"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_wiki_pages", verbose_name=_("owner"))
    last_modifier = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="last_modified_wiki_pages", verbose_name=_("last modifier"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    attachments = GenericRelation("attachments.Attachment")
    _importing = None

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

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)


class WikiLink(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="wiki_links", verbose_name=_("project"))
    title = models.CharField(max_length=500, null=False, blank=False)
    href = models.SlugField(max_length=500, db_index=True, null=False, blank=False,
                            verbose_name=_("href"))
    order = models.BigIntegerField(null=False, blank=False, default=timestamp_ms,
                                             verbose_name=_("order"))

    class Meta:
        verbose_name = "wiki link"
        verbose_name_plural = "wiki links"
        ordering = ["project", "order", "id"]
        unique_together = ("project", "href")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.href:
            with advisory_lock("wiki-page-creation-{}".format(self.project_id)):
                wl_qs = self.project.wiki_links.all()
                self.href = slugify_uniquely_for_queryset(self.title, wl_qs, slugfield="href")
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
