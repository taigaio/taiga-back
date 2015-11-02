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


##########
# MODELS #
##########

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver


class BlockedMixin(models.Model):
    is_blocked = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is blocked"))
    blocked_note = models.TextField(default="", null=False, blank=True,
                                   verbose_name=_("blocked note"))
    class Meta:
        abstract = True


@receiver(models.signals.pre_save, dispatch_uid='blocked_pre_save')
def blocked_pre_save(sender, instance, **kwargs):
    if  isinstance(instance, BlockedMixin) and not instance.is_blocked:
        instance.blocked_note = ""
