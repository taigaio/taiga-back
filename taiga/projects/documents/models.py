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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField
from taiga.base.utils.slug import slugify_uniquely as slugify


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

