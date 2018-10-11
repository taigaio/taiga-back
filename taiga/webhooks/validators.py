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
import ipaddress
from urllib.parse import urlparse

from django.conf import settings
from django.utils.translation import ugettext as _

from taiga.base.api import validators
from taiga.base.exceptions import ValidationError

from .models import Webhook


class WebhookValidator(validators.ModelValidator):
    class Meta:
        model = Webhook

    def validate_url(self, attrs, source):
        if settings.WEBHOOKS_BLOCK_PRIVATE_ADDRESS:
            host = urlparse(attrs[source]).hostname
            try:
                ipa = ipaddress.ip_address(host)
            except ValueError:
                return attrs
            if ipa.is_private:
                raise ValidationError(_("Not allowed IP Address"))
            return attrs
        return attrs
