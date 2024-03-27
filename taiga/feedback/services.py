# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from taiga.base.mails import mail_builder


def send_feedback(feedback_entry, extra, reply_to=[]):
    support_email = settings.FEEDBACK_EMAIL

    if support_email:
        reply_to.append(support_email)

        ctx = {
            "feedback_entry": feedback_entry,
            "extra": extra
        }

        email = mail_builder.feedback_notification(support_email, ctx)
        email.extra_headers["Reply-To"] = ", ".join(reply_to)
        email.send()
