# -*- coding: utf-8 -*-
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
