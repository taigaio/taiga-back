# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from djmail import template_mail
import premailer

import logging


# Hide CSS warnings messages if debug mode is disable
if not getattr(settings, "DEBUG", False):
    premailer.premailer.cssutils.log.setLevel(logging.CRITICAL)


class InlineCSSTemplateMail(template_mail.TemplateMail):
    def make_email_object(self, to, context, **kwargs):
        from taiga.instance_settings import services as instance_settings

        context = dict(context)
        recipient = to if hasattr(to, "lang") else None
        if recipient is None and isinstance(to, str):
            candidate = context.get("user")
            addresses = (getattr(candidate, "email", None),
                         getattr(candidate, "new_email", None))
            if to.lower() in {address.lower() for address in addresses if address}:
                recipient = candidate
        context["lang"] = instance_settings.recipient_language(
            recipient, project_language=context.get("lang"))
        return super().make_email_object(to, context, **kwargs)

    def _render_message_body_as_html(self, context):
        html = super()._render_message_body_as_html(context)

        # Transform CSS into line style attributes
        return premailer.transform(html)


class MagicMailBuilder(template_mail.MagicMailBuilder):
    pass


mail_builder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)
