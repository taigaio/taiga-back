# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from . import services

import uuid

def _generate_uuid():
    return str(uuid.uuid1())


class Application(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, default=_generate_uuid)

    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))

    icon_url = models.TextField(null=True, blank=True, verbose_name=_("Icon url"))
    web = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("web"))
    description = models.TextField(null=True, blank=True, verbose_name=_("description"))

    next_url = models.TextField(null=False, blank=False, verbose_name=_("Next url"))

    class Meta:
        verbose_name = "application"
        verbose_name_plural = "applications"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ApplicationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, null=False,
                                    related_name="application_tokens",
                                    verbose_name=_("user"))

    application = models.ForeignKey("Application", blank=False, null=False,
                                    related_name="application_tokens",
                                    verbose_name=_("application"))

    auth_code = models.CharField(max_length=255, null=True, blank=True, default=None)
    token = models.CharField(max_length=255, null=True, blank=True, default=None)
    # An unguessable random string. It is used to protect against cross-site request forgery attacks.
    state = models.CharField(max_length=255, null=True, blank=True, default="")

    class Meta:
        unique_together = ("application", "user",)

    def __str__(self):
        return "{application}: {user} - {token}".format(application=self.application.name, user=self.user.get_full_name(), token=self.token)

    @property
    def next_url(self):
        return "{url}?auth_code={auth_code}".format(url=self.application.next_url, auth_code=self.auth_code)

    def update_auth_code(self):
        self.auth_code = _generate_uuid()

    def generate_token(self):
        self.auth_code = None
        if not self.token:
            self.token = _generate_uuid()
