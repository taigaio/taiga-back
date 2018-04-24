# Copyright (C) 2018 Miguel González <migonzalvar@gmail.com>
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


class DueDateMixin(models.Model):
    due_date = models.DateField(
        blank=True, null=True, default=None, verbose_name=_('due date'),
    )
    due_date_reason = models.TextField(
        null=False, blank=True, default='', verbose_name=_('reason for the due date'),
    )

    class Meta:
        abstract = True
