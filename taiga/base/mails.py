# -*- coding: utf-8 -*-
from django.conf import settings

from djmail import template_mail
import premailer

import logging


# Hide CSS warnings messages if debug mode is disable
if not getattr(settings, "DEBUG", False):
    premailer.premailer.cssutils.log.setLevel(logging.CRITICAL)


class InlineCSSTemplateMail(template_mail.TemplateMail):
    def _render_message_body_as_html(self, context):
        html = super()._render_message_body_as_html(context)

        # Transform CSS into line style attributes
        return premailer.transform(html)


class MagicMailBuilder(template_mail.MagicMailBuilder):
    pass


mail_builder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)
