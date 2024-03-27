# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import ipaddress
from urllib.parse import urlparse

from django.conf import settings
from django.utils.translation import gettext as _

from taiga.base.api import validators
from taiga.base.exceptions import ValidationError

from .models import Webhook


class WebhookValidator(validators.ModelValidator):
    class Meta:
        model = Webhook

    def validate_url(self, attrs, source):
        if not settings.WEBHOOKS_ALLOW_PRIVATE_ADDRESS:
            host = urlparse(attrs[source]).hostname
            try:
                ipa = ipaddress.ip_address(host)
            except ValueError:
                return attrs
            if ipa.is_private:
                raise ValidationError(_("Not allowed IP Address"))
            return attrs
        return attrs
