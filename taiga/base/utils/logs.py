# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.views.debug import ExceptionReporter
from django.utils.log import AdminEmailHandler
from django.conf import settings
from django import template
from copy import copy


class CustomAdminEmailHandler(AdminEmailHandler):
    def emit(self,record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                ('internal' if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 else 'EXTERNAL'),
                record.getMessage()
            )
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = ExceptionReporter(request, is_email=True, *exc_info)

        error_message ="\n".join(reporter.get_traceback_text().strip().split("GET:")[0].splitlines()[-4:-1])

        message = "%s\n\n%s" % (self.format(no_exc_record), error_message)
        html_message = reporter.get_traceback_html() if self.include_html else None

        self.send_mail(subject, message, fail_silently=True, html_message=html_message)
