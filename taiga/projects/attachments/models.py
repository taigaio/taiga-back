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

import hashlib
import os
import os.path as path

from unidecode import unidecode

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from taiga.base.utils.iterators import split_by_n


def get_attachment_file_path(instance, filename):
    basename = path.basename(filename).lower()
    base, ext = path.splitext(basename)
    base = slugify(unidecode(base))
    basename = "".join([base, ext])

    hs = hashlib.sha256()
    hs.update(force_bytes(timezone.now().isoformat()))
    hs.update(os.urandom(1024))

    p1, p2, p3, p4, *p5 = split_by_n(hs.hexdigest(), 1)
    hash_part = path.join(p1, p2, p3, p4, "".join(p5))

    return path.join("attachments", hash_part, basename)


class Attachment(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=False,
                              related_name="change_attachments",
                              verbose_name=_("owner"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="attachments", verbose_name=_("project"))
    content_type = models.ForeignKey(ContentType, null=False, blank=False,
                                     verbose_name=_("content type"))
    object_id = models.PositiveIntegerField(null=False, blank=False,
                                            verbose_name=_("object id"))
    content_object = generic.GenericForeignKey("content_type", "object_id")
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    name = models.CharField(blank=True, default="", max_length=500)
    size = models.IntegerField(null=True, blank=True, editable=False, default=None)
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                                     upload_to=get_attachment_file_path,
                                     verbose_name=_("attached file"))


    is_deprecated = models.BooleanField(default=False, verbose_name=_("is deprecated"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    order = models.IntegerField(default=0, null=False, blank=False, verbose_name=_("order"))

    _importing = None

    class Meta:
        verbose_name = "attachment"
        verbose_name_plural = "attachments"
        ordering = ["project", "created_date"]
        permissions = (
            ("view_attachment", "Can view attachment"),
        )

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)

    def __str__(self):
        return "Attachment: {}".format(self.id)
