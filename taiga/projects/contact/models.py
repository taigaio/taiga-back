# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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


class ContactEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contact_entries",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )

    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="contact_entries",
        verbose_name=_("project"),
        on_delete=models.CASCADE,
    )

    comment = models.TextField(null=False, blank=False, verbose_name=_("comment"))

    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = "contact entry"
        verbose_name_plural = "contact entries"
        ordering = ["-created_date", "id"]
