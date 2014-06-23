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
from django.utils.translation import ugettext_lazy as _

from taiga.base import exceptions as exc


class OCCResourceMixin(object):
    """
    Rest Framework resource mixin for resources that need to have concurrent
    accesses and editions controlled.
    """
    def pre_save(self, obj):
        current_version = obj.version
        param_version = self.request.DATA.get('version', None)

        if obj.id is not None and current_version != param_version:
            raise exc.WrongArguments({"version": "The version doesn't match with the current one"})

        if obj.id:
            obj.version = models.F('version') + 1

        super().pre_save(obj)


class OCCModelMixin(models.Model):
    """
    Generic model mixin that makes model compatible
    with concurrency control system.
    """
    version = models.IntegerField(null=False, blank=False, default=1, verbose_name=_("version"))

    class Meta:
        abstract = True
