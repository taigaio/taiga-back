# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic


class Votes(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType")
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey("content_type", "object_id")
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Votes")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id")

    def __str__(self):
        return self.count


class Vote(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType")
    object_id = models.PositiveIntegerField(null=False)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                             related_name="votes", verbose_name=_("votes"))

    class Meta:
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id", "user")

    def __str__(self):
        return self.user
