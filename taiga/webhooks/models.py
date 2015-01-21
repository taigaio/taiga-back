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

from django_pgjson.fields import JsonField


class Webhook(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="webhooks")
    name = models.CharField(max_length=250, null=False, blank=False,
                        verbose_name=_("name"))
    url = models.URLField(null=False, blank=False, verbose_name=_("URL"))
    key = models.TextField(null=False, blank=False, verbose_name=_("secret key"))


class WebhookLog(models.Model):
    webhook = models.ForeignKey(Webhook, null=False, blank=False,
                                related_name="logs")
    url = models.URLField(null=False, blank=False, verbose_name=_("URL"))
    status = models.IntegerField(null=False, blank=False, verbose_name=_("Status code"))
    request_data = JsonField(null=False, blank=False, verbose_name=_("Request data"))
    response_data = models.TextField(null=False, blank=False, verbose_name=_("Response data"))
