# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
from django_pgjson.fields import JsonField


class StorageEntry(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, null=False,
                              related_name="storage_entries", verbose_name=_("owner"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    key = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("key"))
    value = JsonField(blank=True, default=None, null=True, verbose_name=_("value"))

    class Meta:
        verbose_name = "storage entry"
        verbose_name_plural = "storages entries"
        unique_together = ("owner", "key")
        ordering = ["owner", "key"]
