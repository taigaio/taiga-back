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
from django.utils.translation import ugettext_lazy as _


class FeedbackEntry(models.Model):
    full_name = models.CharField(null=False, blank=False, max_length=256,
                                 verbose_name=_('full name'))
    email = models.EmailField(null=False, blank=False, max_length=255,
                              verbose_name=_('email address'))
    comment = models.TextField(null=False, blank=False,
                               verbose_name=_("comment"))
    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = "feedback entry"
        verbose_name_plural = "feedback entries"
        ordering = ["-created_date", "id"]
