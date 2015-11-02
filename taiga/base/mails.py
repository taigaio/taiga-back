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
