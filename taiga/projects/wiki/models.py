# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
